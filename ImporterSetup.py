#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the main class responsible for importing the assets and textures and creating materials for them
This Module:
- Converts the json to useable format
- Calls the import functions 
- Calls the material setup functions
- Checks for asset type and setups accordingly
- Checks for the saved UI preferences
- Gives name to the imported mesh
"""


import os, json
import maya.cmds as mc
import maya.mel as melc

#import Megascans.Hypershade

class importerSetup():
    Instance = None
    """set_Asset_Data takes the json data we received from the thread and converts it into
       a friendly structure for all the other functions to use. """

    @staticmethod
    def getInstance():
        if( importerSetup.Instance == None):
            importerSetup()
        return importerSetup.Instance

    def __init__(self):
        importerSetup.Instance = self

# set the exported asset data by using Json provided with the asset
    def set_Asset_Data(self, json_data):
        self.setRenderEngine()
        if(self.Renderer == "Not-Supported"):
            msg = 'Your current render engine (' + self.Renderer + ') is not supported by the Bridge Plugin so we are terminating the import process but the Plugin is still running!'
            mc.confirmDialog( title='MS Plugin Error', message=msg, button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok')
            print (msg)
            return
        else:
            print("Your current render engine is " + self.Renderer)
        self.json_data = json_data
        self.TexturesList = []
        self.Type = self.json_data["type"]
        self.mesh_transforms = []
        self.imported_geo = []
        self.Path = self.json_data["path"]
        # The extra isHighPoly variable 
        self.isHighPoly = bool(self.json_data["activeLOD"] == "high")
        self.activeLOD = self.json_data["activeLOD"]
        self.minLOD = self.json_data["minLOD"]
        self.ID = self.json_data["id"]
        self.height = float(1.0)
        self.isScatterAsset = self.CheckScatterAsset()
        self.isBillboard = self.CheckIsBillboard()
        self.isMultiMat = False
        self.MultiMaterial = self.getMultiMat()
        self.dictSetup = None
        self.defaultShaderList = []

        #self.materialList = []
        
        self.All_textures_ = ["albedo", "displacement", "cavity", "normal", "roughness", "specular", "normalbump", 
                               "ao", "opacity", "translucency", "gloss", "metalness", "bump", "fuzz", "transmission"]

        texturesListName = "components"
        if self.isBillboard:
            texturesListName = "components"

        self.TexturesList = [(obj["format"], obj["type"], obj["path"]) for obj in self.json_data[texturesListName] if obj["type"] in self.All_textures_]

        self.GeometryList = [(obj["format"], obj["path"]) for obj in self.json_data["meshList"]]

        if "name" in self.json_data.keys():
            self.Name = self.json_data["name"].replace(" ", "_")

        else:
            self.Name = os.path.basename(self.json_data["path"]).replace(" ", "_")

            if len(self.Name.split("_")) >= 2:
                self.Name = "_".join(self.Name.split("_")[:-1])

        self.materialName = self.Name + '_' + self.ID

        try:
            if 'meta' in self.json_data.keys():

                meta = self.json_data['meta']
                height_ = [item for item in meta if item["key"].lower() == "height"]
                if len(height_) >= 1:
                    self.height = float( height_[0]["value"].replace('m','') )
        except:
            pass

        self.initAssetImport()

# Sets up the structure and workflow for import. It import the actual geometry ( for scatter as well) and textures and setup material according the render type
    def initAssetImport(self):
        from Megascans import Renderers
        from Megascans import Importer

        plugins_ = [item.lower() for item in mc.pluginInfo( query=True, listPlugins=True )]

        unit_ = mc.currentUnit(q=True)
        mc.currentUnit(l="centimeter")
        warnings = mc.scriptEditorInfo(q=True, suppressWarnings=True)
        mc.scriptEditorInfo(suppressWarnings=True)

        Importer.importGeometryData()
        Importer.importTextureData()
        
        
        if self.Renderer == "Redshift" and "redshift4maya" in plugins_:
            Renderers.Redshift()
            #Hypershade.RearrangeHyperShade()
            #Hypershade.CloseHyperShader()
        elif self.Renderer == "Vray" and "vrayformaya" in plugins_:
            Renderers.Vray()
            #Hypershade.RearrangeHyperShade()
            #Hypershade.CloseHyperShader()
        elif self.Renderer == "Arnold" and "mtoa" in plugins_:
            Renderers.Arnold()
            #Hypershade.RearrangeHyperShade()
            #Hypershade.CloseHyperShader()
        elif self.Renderer == "MayaSoftware":
            Renderers.Arnold()
        else:
            mc.warning(self.Renderer + " was not found, please make sure it's installed.")

        self.ScatterAssetSetup()

        mc.currentUnit(l=unit_)
        mc.scriptEditorInfo(suppressWarnings=warnings)
        
    def getMultiMat(self):
        matId_ = [item for item in self.json_data['meta'] if item["key"].lower() == "materialids"]
        if len(matId_) >=1:
            self.isMultiMat = True
            matList = []
            for data in matId_[0]['value']:
                matList.append(data['material'])
            print(matList)
            return matList
        else:
            return None
        
# Return bool after checking if the asset is type scatter
    def CheckScatterAsset(self):
        if(self.Type == "3d"):
            if('scatter' in self.json_data['categories'] or 'scatter' in self.json_data['tags'] or 'cmb_asset' in self.json_data['categories'] or 'cmb_asset' in self.json_data['tags']):
                # print("It is 3D scatter asset.")
                return True
        return False
    
# Return bool after checking if the asset is type bill board
    def CheckIsBillboard(self):
        # Use billboard textures if importing the Billboard LOD.
        if(self.Type == "3dplant"):
            if (self.activeLOD == self.minLOD):
                # print("It is billboard LOD.")
                return True
        return False
    
# Check the current renderer in maya 
    def setRenderEngine(self):
        selectedRenderer = melc.eval("getAttr defaultRenderGlobals.currentRenderer;")
        selectedRenderer = selectedRenderer.lower()
        self.Renderer = "Not-Supported"
        
        if("redshift" in selectedRenderer):
            self.Renderer = "Redshift"
        elif("vray" in selectedRenderer):
            self.Renderer = "Vray"
        elif("arnold" in selectedRenderer):
            self.Renderer = "Arnold"
        elif("mayasoftware" in selectedRenderer):
            self.Renderer = "MayaSoftware"
            
# Change the import process to scatter type - multiple geometries
    def ScatterAssetSetup(self):
        if self.isScatterAsset and len(self.imported_geo) > 1:
            try:
                self.scatterParentName = self.ID + '_' + self.Name
                self.scatterParentName = mc.group( em=True, name=self.scatterParentName)

                for meshName in self.imported_geo:
                    try:
                        melc.eval('parent '+ meshName +' '+ self.scatterParentName +';')
                    except:
                        pass
            except:
                pass
            
# Creates name for the imported mesh
    def createName(self, meshName):
        shortName = meshName

        try:
            if len(meshName.split("_") ) > 2:
                shortName = [meshName.split("_")[-2], meshName.split("_")[-1]]
                if shortName[0].lower() == self.ID.lower():
                    shortName.remove(shortName[0] )
                shortName = self.Name + '_' + self.ID + "_" + "_".join( shortName )
        except:
            shortName = meshName

        return shortName

# Returns the json structure sent by Bridge
    def getExportStructure(self):       
        return self.json_data

# Save preferences
    def loadApplyToSelection(self):
        if mc.optionVar( exists='QxlApplyToSelection') == 1:
            applyToSelectionFlag = mc.optionVar( q='QxlApplyToSelection')
            if applyToSelectionFlag == 1:
                self.ApplyToSelection = True
            else:
                self.ApplyToSelection = False
        else:
            self.setApplyToSelection(2)
            self.ApplyToSelection = False
        return self.ApplyToSelection

# Returns the bool value
    def getApplyToSelection(self):
        return self.ApplyToSelection

# Check if the bool value was changed
    def updateApplyToSelection(self, flag = False):
        if flag:
            self.setApplyToSelection(1)
            self.ApplyToSelection = True
        else:
            self.setApplyToSelection(2)
            self.ApplyToSelection = False

# Apply the material to the asset
    def setApplyToSelection(self, value):
        mc.optionVar( iv=('QxlApplyToSelection', value))