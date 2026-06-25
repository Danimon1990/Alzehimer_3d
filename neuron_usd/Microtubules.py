from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf

file_path = "output/microtubules.usda"
stage = Usd.Stage.CreateNew(file_path)

world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())

microtube = UsdGeom.Xform.Define(stage, "/World/Microtubule")
microtube.GetPrim().GetReferences().AddReference("../assets/microtubules.usdc")

#scope = materials
UsdGeom.Scope.Define(stage, "/World/Looks")

blue_material = UsdShade.Material.Define(stage, "/World/Looks/BlueMaterial")
blue_shader = UsdShade.Shader.Define(stage, "/World/Looks/BlueMaterial/Shader")
blue_shader.CreateIdAttr("UsdPreviewSurface")
blue_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.0, 0.0, 1.0))
blue_material.CreateSurfaceOutput().ConnectToSource(blue_shader.ConnectableAPI(), "surface")

yellow_material = UsdShade.Material.Define(stage, "/World/Looks/YellowMaterial")
yellow_shader = UsdShade.Shader.Define(stage, "/World/Looks/YellowMaterial/Shader")
yellow_shader.CreateIdAttr("UsdPreviewSurface")
yellow_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1.0, 1.0, 0.0))
yellow_material.CreateSurfaceOutput().ConnectToSource(yellow_shader.ConnectableAPI(), "surface")

stage.Save()