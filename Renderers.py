"""
This Module:
- Handles the material setup for each renderer (Redshift, Vray, Arnold, Octane)
"""
import maya.cmds as mc
import maya.mel as melc

from Megascans.ImporterSetup import importerSetup
instance = importerSetup.getInstance()

#MATERIAL SETUP FUNCTIONS
"""Redshift25_Setup creates a Redshift material setup. """
class Redshift():
    def __init__(self):
        self.shaderList = instance.defaultShaderList
        if instance.isMultiMat:
            for index,shader in enumerate(self.shaderList):
                if instance.MultiMaterial[index].lower() == 'glass':
                    self.GlassSetup(shader)
                else:
                    self.OpaqueSetup(shader)
        else:
            self.OpaqueSetup(None)
    
    def OpaqueSetup(self,shader):
        #print(instance.tex_nodes)
        if len(instance.tex_nodes) >= 1:

            # Create the material and shading group.
            rs_mat = mc.shadingNode('RedshiftMaterial', asShader=True, name=(instance.Name + "_Mat"))
            mc.setAttr(rs_mat+".refl_brdf", 1)
            mc.setAttr(rs_mat+".refl_fresnel_mode", 2)
            #mc.setAttr(rs_mat+".refl_metalness", 0.5)

            if not shader == None:
                rs_sg = shader
            else:
                rs_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=rs_mat, destination=rs_sg)

            # Get a list of all available texture maps. item[1] returns the map type (albedo, normal, etc...).
            maps_ = [item[1] for item in instance.tex_nodes]

            #print(maps_)

            # Create the normal map setup for Redshift.
            if "normal" in maps_:
                rs_normal = mc.shadingNode('RedshiftBumpMap', asShader=True, name=(instance.ID + "_Normal"))

                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                mc.setAttr(rs_normal+".inputType", 1)
                
                if not instance.isHighPoly:
                    mc.setAttr(rs_normal+".scale", 1)
                else:
                    mc.setAttr(rs_normal+".scale", 0.5)

                mc.connectAttr((normal_+".outColor"), (rs_normal+".input"))
                # The normal map is only connected the Redshift material if no displacement is available
                # or if the asset is a 3d plant.
                mc.connectAttr((rs_normal+".out"), (rs_mat+".bump_input"))
                
                '''if "displacement" in maps_:
                    mc.setAttr(rs_normal+".scale", 0)'''


            # If no normal map was found in our texture list we try to find a bump map instead.
            elif "bump" in maps_:
                rs_bump = mc.shadingNode('RedshiftBumpMap', asShader=True, name=(instance.ID + "_BumpNormal"))
                bump_ = [item[0] for item in instance.tex_nodes if item[1] == "bump"][0]
                mc.connectAttr((rs_bump+".out"), (rs_mat+".bump_input"))
                mc.connectAttr((bump_+".outAlpha"), (rs_bump+".input"))
                mc.setAttr(bump_+".alphaIsLuminance", 1)
                mc.setAttr(rs_bump+".scale", 0.05)
                mc.setAttr(rs_bump+".factorInObjScale", 0)
                

            # Create the albedo setup.
            if "albedo" in maps_:
                albedo_ = [item[0] for item in instance.tex_nodes if item[1] == "albedo"][0]
                mc.connectAttr((albedo_+".outColor"), (rs_mat+".diffuse_color"))
                '''if "ao" in maps_:
                    ao_ = [item[0] for item in instance.tex_nodes if item[1] == "ao"][0]
                    
                    md = mc.shadingNode('layeredTexture', asUtility=True, name='layeredTexture')
                    mc.connectAttr((ao_+".outColor"), (md+".inputs[1].color"))
                    mc.setAttr(md+".inputs[1].isVisible", 0)
                    mc.setAttr(md+".inputs[1].blendMode", 6)
                    mc.connectAttr((albedo_+".outColor"), (md+".inputs[2].color"))
                    mc.connectAttr((md+".outColor"), (rs_mat+".diffuse_color"))'''
                
                '''else:
                    mc.connectAttr((albedo_+".outColor"), (rs_mat+".diffuse_color"))'''
        
            # Create the specular setup

            if "metalness" in maps_:    
                metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
                mc.connectAttr((metalness_+".outAlpha"), (rs_mat+".refl_metalness"))
                mc.setAttr(metalness_+".alphaIsLuminance", 1)
                '''if "specular" in maps_:
                    specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                    mc.connectAttr((specular_+".outColor"), (rs_mat+".refl_reflectivity"))'''
            '''elif "specular" in maps_:
                specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                mc.connectAttr((specular_+".outColor"), (rs_mat+".refl_color"))'''
            # Create the roughness setup.
            if "roughness" in maps_:
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outAlpha"), (rs_mat+".refl_roughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)
            elif "gloss" in maps_:
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".outputX"), (rs_mat+".refl_roughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

            # Create the displacement setup.
            if "displacement" in maps_ and not instance.isHighPoly:
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                mc.setAttr(displacement_+".alphaIsLuminance", 1)
                mc.setAttr(displacement_+".alphaOffset", -0.5)
                rs_disp = mc.shadingNode('displacementShader', asShader=True, name=(instance.ID + "_Displacement"))
                mc.connectAttr((rs_disp+".displacement"), (rs_sg+".displacementShader"))
                mc.connectAttr((displacement_+".outAlpha"), (rs_disp+".displacement"))

                mc.setAttr(rs_disp+".scale", 1)

                disp_ext = [item[0] for item in instance.TexturesList if item[1] == "displacement"]
                
                if instance.Type in ["3dplant"]:
                    mc.setAttr(rs_disp+".scale", 0)
                elif instance.Type in ["3d"]:
                    mc.setAttr(rs_disp+".scale", 10)
                    
            # high res case
            else:
                if instance.Type in ["surface"] or instance.Type in ["3dplant"]:
                    displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                    mc.setAttr(displacement_+".alphaIsLuminance", 1)
                    mc.setAttr(displacement_+".alphaOffset", -0.5)
                    rs_disp = mc.shadingNode('displacementShader', asShader=True, name=(instance.ID + "_Displacement"))
                    mc.connectAttr((rs_disp+".displacement"), (rs_sg+".displacementShader"))
                    mc.connectAttr((displacement_+".outAlpha"), (rs_disp+".displacement"))

                    disp_ext = [item[0] for item in instance.TexturesList if item[1] == "displacement"]
                    #print ('Low Res Geo') 
                
                    if instance.Type in ["3dplant"]:
                        mc.setAttr(rs_disp+".scale", 0)
                else:
                    print ('High Res Geo')


            # if len(disp_ext) >= 1 and disp_ext[0].lower() == "exr":
            #     mc.setAttr(rs_disp+".newrange_min", -0.5)
            #     mc.setAttr(rs_disp+".newrange_max", 0.5)
            # else:
                #mc.setAttr(rs_disp+".newrange_min", -1)
                #mc.setAttr(rs_disp+".newrange_max", 1)

                # 3D objects have a displacement scale value of 0.5 while others have a 0.05 value.
                #if instance.Type in ["3dplant"]:
                    #mc.setAttr(rs_disp+".scale", 0)

                #if instance.Type in ["3d"]:
                    #mc.setAttr(rs_disp+".scale", 10)

                #else:
                    #mc.setAttr(rs_disp+".scale", 1)


            # # Create the metalness setup
            # if "metalness" in maps_:
            #     metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
            #     mc.connectAttr((metalness_+".outAlpha"), (rs_mat+".refl_metalness"))


            # Create the translucency setup.
            if "translucency" in maps_:
                #translucency_ = [item[0] for item in instance.tex_nodes if item[1] == "translucency"][0]
                #mc.connectAttr((translucency_+".outColor"), (rs_mat+".transl_color"))
                mc.connectAttr((albedo_+".outColor"), (rs_mat+".transl_color"))
                mc.setAttr(rs_mat + ".transl_weight", 0.5)

            # Create the transmission setup
            elif "transmission" in maps_:
                transmission_ = [item[0] for item in instance.tex_nodes if item[1] == "transmission"][0]
                # mc.connectAttr((transmission_+".outColor.outColorR"), (rs_mat+".transl_weight"))
                # mc.setAttr(rs_mat + ".transl_colorR",1)
                # mc.setAttr(rs_mat + ".transl_colorG",1)
                # mc.setAttr(rs_mat + ".transl_colorB",1)
                
                mc.connectAttr((transmission_+".outColor"), (rs_mat+".refr_transmittance"))
                mc.setAttr(rs_mat + ".ss_amount", 1)
                mc.setAttr(rs_mat + ".ss_scatter_coeff", 0.4,0.4,0.4)


            # Create the opacity setup
            if "opacity" in maps_:
                opacity_ = [item[0] for item in instance.tex_nodes if item[1] == "opacity"][0]
                rs_sprite = mc.shadingNode('RedshiftSprite', asShader=True, name=(instance.ID + "_Sprite"))
                #mc.connectAttr((opacity_+".outColor"), (rs_mat+".opacity_color"))
                mc.setAttr(opacity_+".alphaIsLuminance", 1)
                mc.connectAttr((rs_mat+".outColor"), (rs_sprite+".input"))
                mc.connectAttr((opacity_+".fileTextureName"), (rs_sprite+".tex0"))
                #mc.connectAttr((rs_sprite+".outColor"), (rs_sg+".surfaceShader"))
                mc.defaultNavigation(connectToExisting=True, source=rs_sprite, destination=rs_sg)


            # Go through the list of meshes imported/saved and apply the displacement properties
            # of Redshift on them, then apply the material itinstance.
            if len(instance.mesh_transforms) >= 1:
                for mesh_ in instance.mesh_transforms:


                    if instance.Type in ["3dplant"]:
                        mc.setAttr(mesh_+".rsEnableSubdivision", 0)
                        mc.setAttr(mesh_+".rsEnableDisplacement", 0)
                        mc.setAttr(mesh_+".rsDisplacementScale", 0)
                        mc.setAttr(mesh_+".rsMaxDisplacement", 1)
                        mc.setAttr(mesh_+".rsAutoBumpMap", 0)
                        mc.setAttr(mesh_+".smoothLevel", 1)
                        mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                        mc.setAttr(mesh_+".renderSmoothLevel", 0)
                        mc.setAttr(rs_normal+".scale", 1)
                    
                    elif instance.Type in ["surface"]:
                        mc.setAttr(mesh_+".rsEnableSubdivision", 1)
                        mc.setAttr(mesh_+".rsEnableDisplacement", 1)
                        mc.setAttr(mesh_+".rsScreenSpaceAdaptive", 0)
                        mc.setAttr(mesh_+".rsMinTessellationLength", 0)
                        mc.setAttr(mesh_+".rsMaxTessellationSubdivs", 4)
                        mc.setAttr(mesh_+".rsOutOfFrustumTessellationFactor", 2)
                        mc.setAttr(mesh_+".rsDisplacementScale", 1)
                        mc.setAttr(mesh_+".rsMaxDisplacement", 1)
                        mc.setAttr(mesh_+".rsAutoBumpMap", 1)
                        mc.setAttr(mesh_+".smoothLevel", 1)
                        mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                        mc.setAttr(mesh_+".renderSmoothLevel", 0)

                    elif instance.Type in ["3d"] and not instance.isHighPoly:
                        mc.setAttr(mesh_+".rsEnableSubdivision", 1)
                        mc.setAttr(mesh_+".rsEnableDisplacement", 1)
                        mc.setAttr(mesh_+".rsScreenSpaceAdaptive", 0)
                        mc.setAttr(mesh_+".rsMinTessellationLength", 0)
                        mc.setAttr(mesh_+".rsMaxTessellationSubdivs", 4)
                        mc.setAttr(mesh_+".rsOutOfFrustumTessellationFactor", 2)
                        mc.setAttr(mesh_+".rsDisplacementScale", 1)
                        mc.setAttr(mesh_+".rsMaxDisplacement", 1)
                        mc.setAttr(mesh_+".rsAutoBumpMap", 1)
                        mc.setAttr(mesh_+".smoothLevel", 1)
                        mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                        mc.setAttr(mesh_+".renderSmoothLevel", 0)

                    else:
                        mc.setAttr(mesh_+".rsEnableSubdivision", 0)
                        mc.setAttr(mesh_+".rsScreenSpaceAdaptive", 0)
                        mc.setAttr(mesh_+".rsEnableDisplacement", 0)
                        mc.setAttr(mesh_+".rsMinTessellationLength", 0)
                        mc.setAttr(mesh_+".rsMaxTessellationSubdivs", 0)
                        mc.setAttr(mesh_+".rsOutOfFrustumTessellationFactor", 2)
                        mc.setAttr(mesh_+".rsDisplacementScale", 0)
                        mc.setAttr(mesh_+".rsMaxDisplacement", 1)
                        mc.setAttr(mesh_+".rsAutoBumpMap",0)
                        mc.setAttr(mesh_+".smoothLevel", 1)
                        mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                        mc.setAttr(mesh_+".renderSmoothLevel", 0)

                    if "normal" not in maps_:
                        mc.setAttr(mesh_+".rsAutoBumpMap", 1)

                    mc.select(mesh_)
                    melc.eval('sets -e -forceElement '+rs_sg)

    def GlassSetup(self,shader):
        if len(instance.tex_nodes) >= 1:

            # Create the material and shading group.
            rs_mat = mc.shadingNode('RedshiftMaterial', asShader=True, name=(instance.Name + "_Mat"))
            mc.setAttr(rs_mat+".refl_brdf", 1)
            mc.setAttr(rs_mat+".refl_fresnel_mode", 2)
            #mc.setAttr(rs_mat+".refl_metalness", 0.5)

            if not shader == None:
                rs_sg = shader
            else:
                rs_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=rs_mat, destination=rs_sg)

            # Get a list of all available texture maps. item[1] returns the map type (albedo, normal, etc...).
            maps_ = [item[1] for item in instance.tex_nodes]

            #print(maps_)

            # Create the normal map setup for Redshift.
            if "normal" in maps_:
                rs_normal = mc.shadingNode('RedshiftBumpMap', asShader=True, name=(instance.ID + "_Normal"))

                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                mc.setAttr(rs_normal+".inputType", 1)
                mc.setAttr(rs_normal+".scale", 1)

                mc.connectAttr((normal_+".outColor"), (rs_normal+".input"))
                # The normal map is only connected the Redshift material if no displacement is available
                # or if the asset is a 3d plant.
                mc.connectAttr((rs_normal+".out"), (rs_mat+".bump_input"))
                
                if "displacement" in maps_:
                    mc.setAttr(rs_normal+".scale", 1)


            # If no normal map was found in our texture list we try to find a bump map instead.
            elif "bump" in maps_:
                rs_bump = mc.shadingNode('RedshiftBumpMap', asShader=True, name=(instance.ID + "_BumpNormal"))
                mc.connectAttr((rs_bump+".out"), (rs_mat+".bump_input"))
                mc.setAttr(rs_bump+".scale", 0.05)
                mc.setAttr(rs_bump+".factorInObjScale", 0)

                bump_ = [item[0] for item in instance.tex_nodes if item[1] == "bump"][0]

    
            # Create the roughness setup.
            if "roughness" in maps_:
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outAlpha"), (rs_mat+".refl_roughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)
            elif "gloss" in maps_:
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".outputX"), (rs_mat+".refl_roughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)
                
            mc.setAttr(rs_mat+".refr_weight", 0.85)



#########################################################################################

"""Vray36_Setup creates a V-ray material setup. """

class Vray():
    def __init__(self):
        self.shaderList = instance.defaultShaderList
        if instance.isMultiMat:
            for index,shader in enumerate(self.shaderList):
                if instance.MultiMaterial[index].lower() == 'glass':
                    self.GlassSetup(shader)
                else:
                    self.OpaqueSetup(shader)
        else:
            self.OpaqueSetup(None)
    
    def OpaqueSetup(self,shader):
        if len(instance.tex_nodes) >= 1:

            # Set the material and shading group

            mtl_node = mc.shadingNode('VRayMtl', asShader=True, name=(instance.Name + "_Mat"))
            
            if not shader == None:
                mtl_sg = shader
            else:
                mtl_sg = mc.sets(renderable=True,noSurfaceShader=True,empty=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=mtl_node, destination=mtl_sg)

            maps_ = [item[1] for item in instance.tex_nodes]

            #print(maps_)


            if "normal" in maps_:

                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]

                mc.defaultNavigation(connectToExisting=True, source=normal_, destination=mtl_node + ".bumpMap")
                mc.setAttr(mtl_node + ".bumpMapType", 1)
                mc.setAttr(mtl_node + ".bumpMult", 1)
                mc.setAttr(mtl_node + ".refractionIOR", 1.52)


            if "albedo" in maps_:

                albedo_ = [item[0] for item in instance.tex_nodes if item[1] == "albedo"][0]
                '''
                if "ao" in maps_:
                    ao_ = [item[0] for item in instance.tex_nodes if item[1] == "ao"][0]
                    #md = mc.shadingNode('multiplyDivide', asUtility=True, name='multiplyDivideAO')
                    md = mc.shadingNode('layeredTexture', asUtility=True, name='layeredTexture')
                    mc.connectAttr((ao_+".outColor"), (md+".inputs[1].color"))
                    mc.setAttr(md+".inputs[1].isVisible", 0)
                    mc.setAttr(md+".inputs[1].blendMode", 6)
                    mc.connectAttr((albedo_+".outColor"), (md+".inputs[2].color"))
                    mc.connectAttr((md+".outColor"), (mtl_node+".color"))
                    
                else:
                    mc.defaultNavigation(connectToExisting=True, source=albedo_, destination=mtl_node + ".color")
                mc.vray("addAttributesFromGroup", albedo_, "vray_file_gamma", 1)
                '''
                mc.defaultNavigation(connectToExisting=True, source=albedo_, destination=mtl_node + ".color")
                mc.vray("addAttributesFromGroup", albedo_, "vray_file_gamma", 1)

            
            if "roughness" in maps_:

                microSurface = None

                microSurface = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]

                mc.setAttr(microSurface+".alphaIsLuminance", 1)
                mc.vray("addAttributesFromGroup", microSurface, "vray_file_gamma", 1)

                #if microSurface.lower().endswith("roughness"):
                mc.connectAttr((microSurface+".outAlpha"), (mtl_node+".reflectionGlossiness"))
                mc.setAttr(mtl_node + ".reflectionColorAmount", 1)
                mc.setAttr(mtl_node + ".useRoughness", 1)
                mc.setAttr(mtl_node + ".reflectionColorR", 1.0 )
                mc.setAttr(mtl_node + ".reflectionColorG", 1.0 )
                mc.setAttr(mtl_node + ".reflectionColorB", 1.0 )
            
            '''
            elif "gloss" in maps_:

                microSurface = None

                microSurface = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]

                mc.setAttr(microSurface+".alphaIsLuminance", 1)
                mc.vray("addAttributesFromGroup", microSurface, "vray_file_gamma", 1)

                if microSurface.lower().endswith("gloss"):
                    mc.connectAttr((microSurface+".outAlpha"), (mtl_node+".reflectionGlossiness"))
                    mc.setAttr(mtl_node + ".reflectionColorAmount", 1)
                    mc.setAttr(mtl_node + ".reflectionColorR", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorG", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorB", 1.0 )
            '''
                    
            '''
            if "specular" in maps_:

                specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                mc.defaultNavigation(connectToExisting=True, source=specular_, destination=mtl_node + ".reflectionColor")
                mc.vray("addAttributesFromGroup", specular_, "vray_file_gamma", 1)
            '''


            if "metalness" in maps_:
                metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
                mc.connectAttr((metalness_+".outAlpha"), (mtl_node+".metalness"))
                mc.setAttr(metalness_+".alphaIsLuminance", 1)

            if "displacement" in maps_ and not instance.isHighPoly:
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]

                '''
                mc.defaultNavigation(connectToExisting=True, source=displacement_, destination=mtl_sg + ".displacementShader")
                mc.vray("addAttributesFromGroup", displacement_, "vray_file_allow_neg_colors", 1)
                '''
                vray_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(instance.ID + "_Displacement_shr"))

                mc.connectAttr((displacement_+".outAlpha"), (vray_disp_shr+".displacement"))
                mc.connectAttr((vray_disp_shr+".displacement"), (mtl_sg+".displacementShader"))
                mc.setAttr(vray_disp_shr + ".scale", 10.0)

                mc.vray("addAttributesFromGroup", displacement_, "vray_file_allow_neg_colors", 1)
                mc.setAttr(displacement_+".alphaIsLuminance", 1)
                mc.setAttr(displacement_+".alphaOffset", -0.5)
                print ('Low Res Geo')

                #if instance.Type in ["3dplant"]:
                #    mc.delete(vray_disp_shr)
            
            else:
                if instance.Type in ["surface"]:
                    displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                    vray_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(instance.ID + "_Displacement_shr"))

                    mc.connectAttr((displacement_+".outAlpha"), (vray_disp_shr+".displacement"))
                    mc.connectAttr((vray_disp_shr+".displacement"), (mtl_sg+".displacementShader"))
                    mc.setAttr(vray_disp_shr + ".scale", 10.0)

                    mc.vray("addAttributesFromGroup", displacement_, "vray_file_allow_neg_colors", 1)
                    mc.setAttr(displacement_+".alphaIsLuminance", 1)
                    mc.setAttr(displacement_+".alphaOffset", -0.5)
                    print ('Low Res Geo')
                else:
                    print ('High Res Geo') 

            # if "metalness" in maps_:
            #     metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
            #     mc.connectAttr((metalness_+".outAlpha"), (mtl_node+".refl_metalness"))

            if "translucency" in maps_:
                #translucency_ = [item[0] for item in instance.tex_nodes if item[1] == "translucency"][0]
                #mc.setAttr(mtl_node+".sssOn", 1)
                vray_2sided = mc.shadingNode('VRayMtl2Sided', asTexture=True, name=(instance.ID + "_2Sided"))
                mc.connectAttr((mtl_node+".outColor"), (vray_2sided + ".backMaterial"))
                mc.connectAttr((mtl_node+".outColor"), (vray_2sided + ".frontMaterial"))
                
                mc.disconnectAttr((mtl_node+".outColor"), (mtl_sg + ".surfaceShader"))
                mc.connectAttr((vray_2sided+".outColor"), (mtl_sg + ".surfaceShader"))
                #mc.connectAttr((translucency_+".outColor"), (mtl_node+".translucencyColor"))
                
            
            '''
            if "transmission" in maps_:
                transmission_ = [item[0] for item in instance.tex_nodes if item[1] == "transmission"][0]
                mc.connectAttr((transmission_+".outColor.outColorR"), (mtl_node+".translucencyColorR"))
            '''


            if "opacity" in maps_:
                opacity_ = [item[0] for item in instance.tex_nodes if item[1] == "opacity"][0]
                mc.setAttr(mtl_node+".opacityMode", 1)
                mc.setAttr(mtl_node+".doubleSided", 1)

                mc.defaultNavigation(connectToExisting=True, source=opacity_, destination=mtl_node + ".opacityMap")


            if len(instance.mesh_transforms) >= 1:
                # mesh_ = instance.mesh_transforms[0]
                for mesh_ in instance.mesh_transforms:

                    mc.select(mesh_)
                    shapeNode = mc.ls(sl=True, dag=True, lf=True, o=True, fl=True)

                    mc.setAttr(mesh_+".smoothLevel", 1)

                    if len(shapeNode) == 1:
                        shape = shapeNode[0]

                        if not instance.isHighPoly:
                            
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_displacement" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subdivision" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subquality" 1;')
                            mc.setAttr(mesh_+".vrayDisplacementAmount", keyable=True)
                            mc.setAttr(mesh_+".vrayOverrideGlobalSubQual", keyable=True)
                            mc.setAttr(mesh_+".vraySubdivEnable", keyable=True)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", keyable=True)
                            mc.setAttr(mesh_+".vrayEdgeLength", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", keyable=True)
                            mc.setAttr(mesh_+".vrayViewDep", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 0)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", 6)

                        if instance.Type in ["3d"] and not instance.isHighPoly:
                            mc.connectAttr((shape + ".vrayDisplacementAmount"), (vray_disp_shr + ".scale"))
                            melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 10;')
                            melc.eval('setAttr "' + shape + '.vrayDisplacementShift" 0.0;')
                            
                        elif instance.Type in ["3dplant"] and not instance.isHighPoly:
                            melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 0;')
                            #melc.eval('setAttr "' + shape + '.vrayOverrideGlobalSubQual" 0;')
                            melc.eval('setAttr "' + shape + '.vraySubdivEnable" 0;')
                            #mc.setAttr(mesh_+".vrayMaxSubdivs", 0)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 1)
                        else:
                            if not instance.isHighPoly:
                                mc.connectAttr((shape + ".vrayDisplacementAmount"), (vray_disp_shr + ".scale"))
                                melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 1;')
                                melc.eval('setAttr "' + shape + '.vrayDisplacementShift" 0;')
                        if not instance.isHighPoly:
                            melc.eval('setAttr "' + shape + '.vrayDisplacementKeepContinuity" 1;')
                        
                        if instance.Type in ["surface"]:
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_displacement" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subdivision" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subquality" 1;')
                            mc.setAttr(mesh_+".vrayDisplacementAmount", keyable=True)
                            mc.setAttr(mesh_+".vrayOverrideGlobalSubQual", keyable=True)
                            mc.setAttr(mesh_+".vraySubdivEnable", keyable=True)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", keyable=True)
                            mc.setAttr(mesh_+".vrayEdgeLength", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", keyable=True)
                            mc.setAttr(mesh_+".vrayViewDep", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 0)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", 6)

                    
                    melc.eval('sets -e -forceElement '+mtl_sg)

                    if len(shapeNode) > 1:
                        shape = shapeNode[0]

                        if not instance.isHighPoly:
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_displacement" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subdivision" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subquality" 1;')
                            #mc.setAttr(mesh_+".vrayDisplacementAmount", keyable=True)
                            mc.setAttr(mesh_+".vrayOverrideGlobalSubQual", keyable=True)
                            mc.setAttr(mesh_+".vraySubdivEnable", keyable=True)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", keyable=True)
                            mc.setAttr(mesh_+".vrayEdgeLength", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", keyable=True)
                            mc.setAttr(mesh_+".vrayViewDep", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 0)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", 6)

                        if instance.Type in ["3d"] and not instance.isHighPoly:
                            melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 10;')
                            melc.eval('setAttr "' + shape + '.vrayDisplacementShift" 0.0;')
                        
                        elif instance.Type in ["3dplant"] and not instance.isHighPoly:
                            melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 0;')
                            melc.eval('setAttr "' + shape + '.vrayOverrideGlobalSubQual" 0;')
                            melc.eval('setAttr "' + shape + '.vraySubdivEnable" 0;')
                            mc.setAttr(mesh_+".vrayMaxSubdivs", 0)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 1)
                        else:
                            if not instance.isHighPoly:
                                melc.eval('setAttr "' + shape + '.vrayDisplacementAmount" 1;')
                                melc.eval('setAttr "' + shape + '.vrayDisplacementShift" 0;')

                        if not instance.isHighPoly:
                            melc.eval('setAttr "' + shape + '.vrayDisplacementKeepContinuity" 1;')
                        
                        if instance.Type in ["surface"]:
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_displacement" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subdivision" 1;')
                            melc.eval('vray addAttributesFromGroup "' + shape + '" "vray_subquality" 1;')
                            mc.setAttr(mesh_+".vrayDisplacementAmount", keyable=True)
                            mc.setAttr(mesh_+".vrayOverrideGlobalSubQual", keyable=True)
                            mc.setAttr(mesh_+".vraySubdivEnable", keyable=True)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", keyable=True)
                            mc.setAttr(mesh_+".vrayEdgeLength", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", keyable=True)
                            mc.setAttr(mesh_+".vrayViewDep", keyable=True)
                            mc.setAttr(mesh_+".vrayDisplacementNone", 0)
                            mc.setAttr(mesh_+".vrayMaxSubdivs", 6)

                    melc.eval('sets -e -forceElement '+mtl_sg)
                    
    def GlassSetup(self,shader):
        if len(instance.tex_nodes) >= 1:

            # Set the material and shading group

            mtl_node = mc.shadingNode('VRayMtl', asShader=True, name=(instance.Name + "_Mat"))
           
            if not shader == None:
                mtl_sg = shader
            else:
                mtl_sg = mc.sets(renderable=True,noSurfaceShader=True,empty=True, name=(instance.Name + "_SG"))
            
            
            mc.defaultNavigation(connectToExisting=True, source=mtl_node, destination=mtl_sg)

            maps_ = [item[1] for item in instance.tex_nodes]

            #print(maps_)


            if "normal" in maps_:

                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]

                mc.defaultNavigation(connectToExisting=True, source=normal_, destination=mtl_node + ".bumpMap")
                mc.setAttr(mtl_node + ".bumpMapType", 1)


            if "roughness" in maps_:

                microSurface = None

                microSurface = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]

                mc.setAttr(microSurface+".alphaIsLuminance", 1)
                mc.vray("addAttributesFromGroup", microSurface, "vray_file_gamma", 1)

                if microSurface.lower().endswith("roughness"):


                    mc.connectAttr((microSurface+".outColor.outColorR"), (mtl_node+".reflectionGlossiness"))
                    mc.setAttr(mtl_node + ".reflectionColorAmount", 1)
                    mc.setAttr(mtl_node + ".useRoughness", 1)
                    mc.setAttr(mtl_node + ".reflectionColorR", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorG", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorB", 1.0 )
            
            elif "gloss" in maps_:

                microSurface = None

                microSurface = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]

                mc.setAttr(microSurface+".alphaIsLuminance", 1)
                mc.vray("addAttributesFromGroup", microSurface, "vray_file_gamma", 1)

                if microSurface.lower().endswith("gloss"):
                    mc.connectAttr((microSurface+".outColor.outColorR"), (mtl_node+".reflectionGlossiness"))
                    mc.setAttr(mtl_node + ".reflectionColorAmount", 1)
                    mc.setAttr(mtl_node + ".reflectionColorR", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorG", 1.0 )
                    mc.setAttr(mtl_node + ".reflectionColorB", 1.0 )       
                    

            mc.setAttr(mtl_node + ".refractionColorR", 0.9 )
            mc.setAttr(mtl_node + ".refractionColorG", 0.9 )
            mc.setAttr(mtl_node + ".refractionColorB", 0.9 )  

            
#########################################################################################

"""Arnold3_Setup creates a Arnold material setup."""

class Arnold():
    def __init__(self):
        self.shaderList = instance.defaultShaderList
        self.ShaderName = ""
        if instance.isMultiMat:
            for index,shader in enumerate(self.shaderList):
                if instance.MultiMaterial[index].lower() == 'glass':
                    self.GlassSetup(shader)
                else:
                    self.OpaqueSetup(shader)
        else:
            self.OpaqueSetup(None)
            
    def OpaqueSetup(self, shader):        
        nodes_ = mc.allNodeTypes()
        # print(nodes_)
        
        #Standard Surface is not available in 2019 and 2018
        #if "standardSurface" in nodes_:
        #    self.ShaderName = "standardSurface"
        # else:
        self.ShaderName = "aiStandardSurface"
        
        if len(instance.tex_nodes) >= 1 and self.ShaderName in nodes_:

            # Set the material and shading group

            arn_mat = mc.shadingNode(self.ShaderName, asShader=True, name=(instance.Name + "_Mat"))
            mc.setAttr(arn_mat+".base", 1)
            mc.setAttr(arn_mat+".specular", 1)
            
            if not shader == None:
                arn_sg = shader
            else:
                arn_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=arn_mat, destination=arn_sg)

            maps_ = [item[1] for item in instance.tex_nodes]
            used_maps = []

            # print(maps_)


            if "normal" in maps_:
                arn_normal = mc.shadingNode('aiNormalMap', asShader=True, name=(instance.ID + "_Normal"))
                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                mc.connectAttr((arn_normal+".outValue"), (arn_mat+".normalCamera"))
                mc.connectAttr((normal_+".outColor"), (arn_normal+".input"))
                if not instance.isHighPoly:
                    mc.setAttr(arn_normal+".strength", 0.25)
                else:
                    mc.setAttr(arn_normal+".strength", 0.25)
                
                used_maps.append(arn_normal)


            if "albedo" in maps_:
                albedo_ = [item[0] for item in instance.tex_nodes if item[1] == "albedo"][0]
                '''
                if "ao" in maps_:
                    ao_ = [item[0] for item in instance.tex_nodes if item[1] == "ao"][0]
                    #md = mc.shadingNode('multiplyDivide', asUtility=True, name='multiplyDivideAO')
                    md = mc.shadingNode('layeredTexture', asUtility=True, name='layeredTexture')
                    mc.connectAttr((ao_+".outColor"), (md+".inputs[1].color"))
                    mc.setAttr(md+".inputs[1].isVisible", 0)
                    mc.setAttr(md+".inputs[1].blendMode", 6)
                    mc.connectAttr((albedo_+".outColor"), (md+".inputs[2].color"))
                    mc.connectAttr((md+".outColor"), (arn_mat+".baseColor"))
                else:
                    mc.connectAttr((albedo_+".outColor"), (arn_mat+".baseColor"))
                '''
                mc.connectAttr((albedo_+".outColor"), (arn_mat+".baseColor"))

                used_maps.append(albedo_)

            # Create the specular setup
            '''
            if "specular" in maps_:
                specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                mc.connectAttr((specular_+".outColor"), (arn_mat+".specularColor"))
                mc.setAttr(arn_mat + ".specular",0.5)
            '''

            if "roughness" in maps_:
                #arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outAlpha"), (arn_mat+".specularRoughness"))
                #mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)

                used_maps.append(roughness_)
            '''
            elif "gloss" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".output"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

                used_maps.append(gloss_)
            '''

            if "displacement" in maps_ and not instance.isHighPoly:
                arn_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(instance.ID + "_Displacement_shr"))
                
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                mc.connectAttr((displacement_+".outAlpha"), (arn_disp_shr+".displacement"))
                mc.connectAttr((arn_disp_shr+".displacement"), (arn_sg+".displacementShader"))
                mc.setAttr(arn_disp_shr + ".aiDisplacementAutoBump", 0)
                mc.setAttr(arn_disp_shr + ".aiDisplacementZeroValue", 0)
                mc.setAttr(arn_disp_shr + ".aiDisplacementPadding", 10.0)
                mc.setAttr(arn_disp_shr + ".scale", 10)
                mc.setAttr(displacement_+".alphaIsLuminance", 1)
                mc.setAttr(displacement_+".alphaOffset", -0.5)

                '''
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                mc.connectAttr((displacement_+".outColor"), (arn_sg+".displacementShader"))
                mc.setAttr(displacement_+".alphaIsLuminance", 1)
                '''
                print ('Low Res Geo')

                if instance.Type in ["3dplant"]:
                    mc.delete(arn_disp_shr)
                    

                used_maps.append(displacement_)
            else:
                if instance.Type in ["surface"]:
                    arn_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(instance.ID + "_Displacement_shr"))
                
                    displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                    mc.connectAttr((displacement_+".outAlpha"), (arn_disp_shr+".displacement"))
                    mc.connectAttr((arn_disp_shr+".displacement"), (arn_sg+".displacementShader"))
                    mc.setAttr(arn_disp_shr + ".aiDisplacementAutoBump", 0)
                    mc.setAttr(arn_disp_shr + ".aiDisplacementZeroValue", 0)
                    mc.setAttr(arn_disp_shr + ".aiDisplacementPadding", 10.0)
                    mc.setAttr(arn_disp_shr + ".scale", 10)
                    mc.setAttr(displacement_+".alphaIsLuminance", 1)
                    mc.setAttr(displacement_+".alphaOffset", -0.5)
                else:    
                    print ('High Res Geo')


            if "metalness" in maps_:
                metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
                mc.connectAttr((metalness_+".outAlpha"), (arn_mat+".metalness"))
                mc.setAttr(metalness_+".alphaIsLuminance", 1)

                used_maps.append(metalness_)


            if "translucency" in maps_:
                translucency_ = [item[0] for item in instance.tex_nodes if item[1] == "translucency"][0]
                #mc.connectAttr((translucency_+".outColor"), (arn_mat+".subsurfaceColor"))
                mc.connectAttr((albedo_+".outColor"), (arn_mat+".subsurfaceColor"))
                mc.setAttr(arn_mat+".subsurface", 0.33)
                mc.setAttr(arn_mat+".thinWalled", 1)
                mc.setAttr(arn_mat+".subsurfaceType", 2)

                used_maps.append(translucency_)

            elif "transmission" in maps_:
                transmission_ = [item[0] for item in instance.tex_nodes if item[1] == "transmission"][0]
                mc.connectAttr((transmission_+".outColor.outColorR"), (arn_mat+".transmission"))

                used_maps.append(transmission_)
                

            if "opacity" in maps_:
                opacity_ = [item[0] for item in instance.tex_nodes if item[1] == "opacity"][0]
                mc.connectAttr((opacity_+".outColor"), (arn_mat+".opacity"))
                mc.setAttr(opacity_+".alphaIsLuminance", 1)
                mc.setAttr(arn_mat+".thinWalled", 1)

                used_maps.append(opacity_)

            if len(instance.mesh_transforms) >= 1:
                for mesh_ in instance.mesh_transforms:
                    
                    mc.setAttr(mesh_+".smoothLevel", 1)
                    print(mesh_)

                    if "displacement" in maps_:
                        if not instance.isHighPoly:
                            mc.setAttr(mesh_+".aiSubdivType", keyable=True)
                            mc.setAttr(mesh_+".aiSubdivIterations", keyable=True)
                            mc.setAttr(mesh_+".aiDispAutobump", keyable=True)
                            mc.setAttr(mesh_+".aiSubdivType", 1)
                            if instance.Type in ["3d"]:
                                mc.setAttr(mesh_+".aiSubdivIterations", 3)
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0.0)
                                mc.setAttr(mesh_+".aiDispPadding", 1.0)
                                mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                                mc.setAttr(mesh_+".renderSmoothLevel", 0)
                            elif instance.Type in ["3dplant"]:
                                mc.setAttr(mesh_+".aiSubdivType", 0)
                                mc.setAttr(mesh_+".aiSubdivIterations", 0)
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0.0)
                                mc.setAttr(mesh_+".aiDispPadding", 1.0)
                                mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                                mc.setAttr(mesh_+".renderSmoothLevel", 0)
                                mc.setAttr(arn_normal+".strength", 1)
                                #mc.setAttr(arn_disp_shr + ".scale", 0)
                            else:
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0)
                                mc.setAttr(mesh_+".aiDispPadding", 0.0)
                        
                        if instance.Type in ["surface"]:
                                mc.setAttr(mesh_+".aiSubdivType", keyable=True)
                                mc.setAttr(mesh_+".aiSubdivIterations", keyable=True)
                                mc.setAttr(mesh_+".aiDispAutobump", keyable=True)
                                mc.setAttr(mesh_+".aiSubdivType", 1)
                                mc.setAttr(mesh_+".aiSubdivIterations", 3)

                    if "opacity" in maps_:
                        mc.setAttr(mesh_+".aiOpaque", 0)

                    if "normal" not in maps_ and not instance.isHighPoly:
                        mc.setAttr(mesh_+".aiDispAutobump", 1)
                    
                    mc.select(mesh_)
                    melc.eval('sets -e -forceElement '+arn_sg)
                    
            #print(used_maps)
        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")
    
    def GlassSetup(self, shader):
        nodes_ = mc.allNodeTypes()
        #print(nodes_)
        
        if "standardSurface" in nodes_:
            self.ShaderName = "standardSurface"
        else:
            self.ShaderName = "aiStandardSurface"
        
        if len(instance.tex_nodes) >= 1 and self.ShaderName in nodes_:

            # Set the material and shading group

            arn_mat = mc.shadingNode(self.ShaderName, asShader=True, name=(instance.Name + "_Mat"))
            if not shader == None:
                arn_sg = shader
            else:
                arn_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=arn_mat, destination=arn_sg)

            maps_ = [item[1] for item in instance.tex_nodes]
            used_maps = []

            #print(maps_)


            if "normal" in maps_:
                arn_normal = mc.shadingNode('aiNormalMap', asShader=True, name=(instance.ID + "_Normal"))
                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                mc.connectAttr((arn_normal+".outValue"), (arn_mat+".normalCamera"))
                mc.connectAttr((normal_+".outColor"), (arn_normal+".input"))

                used_maps.append(arn_normal)

            if "roughness" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outColor"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)

                used_maps.append(roughness_)
            elif "gloss" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".output"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

                used_maps.append(gloss_)
                    
            mc.setAttr(arn_mat+".transmission", 0.85)

            #print(used_maps)
        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")

#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
# This section is written by Denes Dankhazi

"""OctaneRender Studio 2021.1.6 - 20.23 Material Creation."""

class OctaneRender():
    def __init__(self):
        self.shaderList = instance.defaultShaderList
        self.ShaderName = ""
        if instance.isMultiMat:
            for index,shader in enumerate(self.shaderList):
                if instance.MultiMaterial[index].lower() == 'glass':
                    self.GlassSetup(shader)
                else:
                    self.OpaqueSetup(shader)
        else:
            self.OpaqueSetup(None)
        
            
    def OpaqueSetup(self, shader):        
        nodes_ = mc.allNodeTypes()
        # print(nodes_)
        
        #Standard Surface is not available in 2019 and 2018
        #if "standardSurface" in nodes_:
        #    self.ShaderName = "standardSurface"
        # else:
        self.ShaderName = "octaneUniversalMaterial"
        
        if len(instance.tex_nodes) >= 1 and self.ShaderName in nodes_:

            # Set the material and shading group

            oct_mat = mc.shadingNode(self.ShaderName, asShader=True, name=(instance.Name + "_Mat"))
            mc.setAttr(oct_mat+".BsdfModel", 6)
            
            octUVTransform_ = mc.shadingNode('octaneTransform2D', asTexture=True, name= 'UVTransform')
            uvCoord_ = instance.coord_2d
            mc.connectAttr((uvCoord_+".rotateUV"), (octUVTransform_+".RotationX"))
            mc.connectAttr((uvCoord_+".offsetU"), (octUVTransform_+".TranslationX"))
            mc.connectAttr((uvCoord_+".offsetV"), (octUVTransform_+".TranslationY"))


            octUVScaleConv_ = mc.shadingNode('multiplyDivide', asTexture=True, name= 'UVScaleConverter')
            mc.setAttr(octUVScaleConv_+".input1X", 1)
            mc.setAttr(octUVScaleConv_+".input1Y", 1)
            mc.setAttr(octUVScaleConv_+".operation", 2)
            mc.connectAttr((uvCoord_+".repeatU"), (octUVScaleConv_+".input2X"))
            mc.connectAttr((uvCoord_+".repeatV"), (octUVScaleConv_+".input2Y"))

            mc.connectAttr((octUVScaleConv_+".outputX"), (octUVTransform_+".ScaleX"))
            mc.connectAttr((octUVScaleConv_+".outputY"), (octUVTransform_+".ScaleY"))
            

            if not shader == None:
                arn_sg = shader
            else:
                arn_sg = mc.sets(r=True, nss=True, name=(instance.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=oct_mat, destination=arn_sg)

            maps_ = [item[1] for item in instance.tex_nodes]
            used_maps = []

            # print(maps_)


            
            if "normal" in maps_:
                #arn_normal = mc.shadingNode('aiNormalMap', asShader=True, name=(instance.ID + "_Normal"))
                normal_ = [item[0] for item in instance.tex_nodes if item[1] == "normal"][0]
                
                octNormal_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'normalMap')
                mc.connectAttr((normal_+".fileTextureName"), (octNormal_+".File"))
                mc.setAttr(octNormal_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octNormal_+".Transform"))
                
                mc.connectAttr((octNormal_+".outTex"), (oct_mat+".Normal"))

                used_maps.append(normal_)


            if "albedo" in maps_:
                albedo_ = [item[0] for item in instance.tex_nodes if item[1] == "albedo"][0]
                
                octAlbedo_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'albedoMap')
                mc.connectAttr((albedo_+".fileTextureName"), (octAlbedo_+".File"))

                mc.connectAttr((octUVTransform_+".outTransform"), (octAlbedo_+".Transform"))

                mc.connectAttr((octAlbedo_+".outTex"), (oct_mat+".Albedo"))

                used_maps.append(albedo_)

            # Create the specular setup
            '''
            if "specular" in maps_:
                specular_ = [item[0] for item in instance.tex_nodes if item[1] == "specular"][0]
                mc.connectAttr((specular_+".outColor"), (oct_mat+".specularColor"))
                mc.setAttr(oct_mat + ".specular",0.5)
            '''
            
            if "roughness" in maps_:
                #arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                roughness_ = [item[0] for item in instance.tex_nodes if item[1] == "roughness"][0]
                
                octRoughness_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'roughnessMap')
                mc.connectAttr((roughness_+".fileTextureName"), (octRoughness_+".File"))
                mc.setAttr(octRoughness_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octRoughness_+".Transform"))

                mc.connectAttr((octRoughness_+".outTex"), (oct_mat+".Roughness"))

                used_maps.append(roughness_)
            '''
            elif "gloss" in maps_:
                arn_rough_range = mc.shadingNode('aiRange', asShader=True, name=(instance.ID + "_Rough_Range"))
                reverse_ = mc.shadingNode('reverse', asShader=True, name= 'invert')
                gloss_ = [item[0] for item in instance.tex_nodes if item[1] == "gloss"][0]
                mc.connectAttr((gloss_+".outColor"), (reverse_+".input"))
                mc.connectAttr((reverse_+".output"), (arn_rough_range+".input"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (oct_mat+".specularRoughness"))
                mc.setAttr(gloss_+".alphaIsLuminance", 1)

                used_maps.append(gloss_)
            '''

            if "displacement" in maps_ and not instance.isHighPoly:
                arn_disp_shr = mc.shadingNode('octaneVertexDisplacementNode', asTexture=True, name=(instance.ID + "_Displacement_shr"))
                mc.setAttr(arn_disp_shr+".MidLevel", 0.5)
                mc.setAttr(arn_disp_shr+".SubdLevel", 3)
                mc.setAttr(arn_disp_shr+".AutoBumpMap", 1)
                mc.setAttr(arn_disp_shr+".Height", 10)

                
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                octDisplacement_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'displaceMap')

                mc.connectAttr((displacement_+".fileTextureName"), (octDisplacement_+".File"))
                mc.connectAttr((octDisplacement_+".outTex"), (arn_disp_shr+".Texture"))
                mc.setAttr(octDisplacement_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octDisplacement_+".Transform"))

                mc.connectAttr((arn_disp_shr+".outDisp"), (oct_mat+".Displacement"))

                '''
                displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                mc.connectAttr((displacement_+".outColor"), (arn_sg+".displacementShader"))
                mc.setAttr(displacement_+".alphaIsLuminance", 1)
                '''
                print ('Low Res Geo')

                if instance.Type in ["3dplant"]:
                    mc.delete(arn_disp_shr)
                    

                used_maps.append(displacement_)
            else:
                if instance.Type in ["surface"]:
                    arn_disp_shr = mc.shadingNode('octaneVertexDisplacementNode', asTexture=True, name=(instance.ID + "_Displacement_shr"))
                    mc.setAttr(arn_disp_shr+".MidLevel", 0.5)
                    mc.setAttr(arn_disp_shr+".SubdLevel", 3)
                    mc.setAttr(arn_disp_shr+".AutoBumpMap", 1)
                    mc.setAttr(arn_disp_shr+".Height", 10)
                    
                    displacement_ = [item[0] for item in instance.tex_nodes if item[1] == "displacement"][0]
                    octDisplacement_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'displaceMap')

                    mc.connectAttr((displacement_+".fileTextureName"), (octDisplacement_+".File"))
                    mc.connectAttr((octDisplacement_+".outTex"), (arn_disp_shr+".Texture"))
                    mc.setAttr(octDisplacement_+".Gamma", 1)

                    mc.connectAttr((octUVTransform_+".outTransform"), (octDisplacement_+".Transform"))

                    mc.connectAttr((arn_disp_shr+".outDisp"), (oct_mat+".Displacement"))
                else:    
                    print ('High Res Geo')


            if "metalness" in maps_:
                metalness_ = [item[0] for item in instance.tex_nodes if item[1] == "metalness"][0]
                
                octMetalness_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'metalnessMap')
                mc.connectAttr((metalness_+".fileTextureName"), (octMetalness_+".File"))
                mc.setAttr(octMetalness_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octMetalness_+".Transform"))

                mc.connectAttr((octMetalness_+".outTex"), (oct_mat+".Metallic"))

                used_maps.append(metalness_)


            if "translucency" in maps_:
                translucency_ = [item[0] for item in instance.tex_nodes if item[1] == "translucency"][0]
                
                mc.setAttr(oct_mat+".TransmissionType", 3)

                octTanslucency_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'translucencyMap')
                mc.connectAttr((translucency_+".fileTextureName"), (octTanslucency_+".File"))
                mc.setAttr(octTanslucency_+".Gamma", 2.2)

                octTranslucencyPower_ = mc.shadingNode('octaneFloatTexture', asTexture=True, name= 'translPower')
                mc.setAttr(octTranslucencyPower_+".Value", 0.05)
                
                mc.connectAttr((octTranslucencyPower_+".outTex"), (octTanslucency_+".Power"))

                mc.connectAttr((octUVTransform_+".outTransform"), (octTanslucency_+".Transform"))

                mc.connectAttr((octTanslucency_+".outTex"), (oct_mat+".Transmission"))

                used_maps.append(translucency_)

            '''
            elif "transmission" in maps_:
                transmission_ = [item[0] for item in instance.tex_nodes if item[1] == "transmission"][0]
                
                octTransmission_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'transmissionMap')
                mc.connectAttr((transmission_+".fileTextureName"), (octTransmission_+".File"))
                mc.setAttr(octTransmission_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octTransmission_+".Transform"))

                mc.connectAttr((octOpacity_+".outTex"), (oct_mat+".Opacity"))

                used_maps.append(transmission_)
            '''
            
                
            
            if "opacity" in maps_:
                opacity_ = [item[0] for item in instance.tex_nodes if item[1] == "opacity"][0]
                
                octOpacity_ = mc.shadingNode('octaneImageTexture', asTexture=True, name= 'opacityMap')
                mc.connectAttr((opacity_+".fileTextureName"), (octOpacity_+".File"))
                mc.setAttr(octOpacity_+".Gamma", 1)

                mc.connectAttr((octUVTransform_+".outTransform"), (octOpacity_+".Transform"))

                mc.connectAttr((octOpacity_+".outTex"), (oct_mat+".Opacity"))

                used_maps.append(opacity_)
            

            if len(instance.mesh_transforms) >= 1:
                for mesh_ in instance.mesh_transforms:
                    
                    mc.setAttr(mesh_+".smoothLevel", 1)
                    print(mesh_)

                    '''
                    if "displacement" in maps_:
                        if not instance.isHighPoly:
                            
                            mc.setAttr(mesh_+".aiSubdivType", keyable=True)
                            mc.setAttr(mesh_+".aiSubdivIterations", keyable=True)
                            mc.setAttr(mesh_+".aiDispAutobump", keyable=True)
                            mc.setAttr(mesh_+".aiSubdivType", 1)
                            if instance.Type in ["3d"]:
                                mc.setAttr(mesh_+".aiSubdivIterations", 3)
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0.0)
                                mc.setAttr(mesh_+".aiDispPadding", 1.0)
                                mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                                mc.setAttr(mesh_+".renderSmoothLevel", 0)
                            elif instance.Type in ["3dplant"]:
                                mc.setAttr(mesh_+".aiSubdivType", 0)
                                mc.setAttr(mesh_+".aiSubdivIterations", 0)
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0.0)
                                mc.setAttr(mesh_+".aiDispPadding", 1.0)
                                mc.setAttr(mesh_+".useSmoothPreviewForRender", 0)
                                mc.setAttr(mesh_+".renderSmoothLevel", 0)
                                mc.setAttr(arn_normal+".strength", 1)
                                #mc.setAttr(arn_disp_shr + ".scale", 0)
                            else:
                                mc.setAttr(mesh_+".aiDispHeight", 1)
                                mc.setAttr(mesh_+".aiDispZeroValue", 0)
                                mc.setAttr(mesh_+".aiDispPadding", 0.0)
                        
                        if instance.Type in ["surface"]:
                                mc.setAttr(mesh_+".aiSubdivType", keyable=True)
                                mc.setAttr(mesh_+".aiSubdivIterations", keyable=True)
                                mc.setAttr(mesh_+".aiDispAutobump", keyable=True)
                                mc.setAttr(mesh_+".aiSubdivType", 1)
                                mc.setAttr(mesh_+".aiSubdivIterations", 3)
                    '''

                    '''
                    if "opacity" in maps_:
                        #mc.setAttr(mesh_+".aiOpaque", 0)

                    if "normal" not in maps_ and not instance.isHighPoly:
                        #mc.setAttr(mesh_+".aiDispAutobump", 1)
                    '''
                    mc.select(mesh_)
                    melc.eval('sets -e -forceElement '+arn_sg)
                    
            #print(used_maps)
        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")
