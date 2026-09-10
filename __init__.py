bl_info = {
    "name": "HERBIE - UV Organizer",
    "author": "HERBIE Dev",
    "version": (1, 7),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > Herbie",
    "description": "Herramientas de mapeo, empaque automático y control de densidades por material.",
    "category": "UV",
}

import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
import random
import os
import bpy.utils.previews
import base64
import tempfile

_herbie_draw_handler = None
custom_icons = None

SVG_DATA = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="1280.000000pt" height="1280.000000pt" viewBox="0 0 1280.000000 1280.000000"
 preserveAspectRatio="xMidYMid meet">

<g transform="translate(0.000000,1280.000000) scale(0.100000,-0.100000)"
fill="#ffffff" stroke="none">
<path d="M5685 12793 c-634 -85 -1203 -234 -1790 -470 -440 -177 -1111 -595
-1584 -986 -1293 -1070 -2044 -2463 -2291 -4249 -18 -131 -20 -200 -20 -597 0
-330 4 -489 15 -602 151 -1502 719 -2766 1749 -3888 182 -198 264 -276 463
-434 867 -691 1752 -1134 2708 -1356 1032 -239 2155 -200 3300 114 355 98 487
151 905 361 741 372 1325 793 1855 1335 451 463 778 926 1079 1529 340 683
553 1411 678 2320 20 143 23 206 23 480 0 330 -10 464 -60 860 -63 485 -109
686 -265 1145 -642 1884 -1793 3183 -3455 3898 -532 229 -1118 397 -1771 507
l-234 40 -637 -1 c-351 -1 -651 -4 -668 -6z m930 -983 c1053 -64 1936 -342
2722 -857 568 -372 1098 -909 1521 -1541 259 -387 434 -705 516 -937 603
-1715 512 -3259 -274 -4630 -283 -492 -627 -926 -1105 -1393 -233 -228 -293
-276 -535 -437 -819 -544 -1632 -851 -2510 -950 -195 -22 -680 -31 -896 -16
-669 47 -1476 251 -1973 501 -1719 861 -2746 2279 -3050 4210 -38 245 -36 771
4 1182 181 1811 1103 3222 2755 4216 346 208 990 447 1527 566 250 56 369 77
483 85 159 12 624 12 815 1z"/>
<path d="M5900 11219 c-309 -19 -977 -200 -1387 -375 -806 -344 -1450 -841
-1954 -1509 -272 -360 -529 -826 -653 -1184 -551 -1589 -378 -3064 519 -4416
195 -295 283 -404 489 -610 763 -761 1577 -1224 2470 -1405 850 -173 1758 -84
2733 268 l182 65 6 41 c13 96 23 1022 15 1431 -9 431 -25 879 -36 961 l-5 42
-187 8 c-103 5 -945 9 -1872 9 -1540 0 -2262 -8 -2841 -31 l-156 -6 -7 23
c-13 42 -19 440 -8 533 l10 89 1994 1996 c2310 2313 3439 3450 3446 3470 2 5
-21 29 -50 55 -39 34 -89 62 -194 106 -556 234 -1080 368 -1664 425 -192 19
-656 27 -850 14z"/>
<path d="M9563 8538 c5 -1247 18 -2174 32 -2243 2 -11 4 -129 4 -262 l1 -243
478 0 c456 0 1030 14 1041 26 28 27 51 762 32 1014 -36 482 -125 901 -284
1325 -217 584 -588 1163 -1047 1639 -103 106 -125 125 -131 109 -6 -14 -8 -13
-8 9 -1 35 -44 68 -89 68 l-35 0 6 -1442z m114 1210 c-2 -18 -4 -6 -4 27 0 33
2 48 4 33 2 -15 2 -42 0 -60z m-10 -180 c-2 -18 -4 -6 -4 27 0 33 2 48 4 33 2
-15 2 -42 0 -60z m-10 -185 c-2 -21 -4 -6 -4 32 0 39 2 55 4 38 2 -18 2 -50 0
-70z m-10 -220 c-2 -21 -4 -4 -4 37 0 41 2 58 4 38 2 -21 2 -55 0 -75z m-10
-210 c-2 -21 -4 -6 -4 32 0 39 2 55 4 38 2 -18 2 -50 0 -70z m-10 -276 c-2
-23 -3 -1 -3 48 0 50 1 68 3 42 2 -26 2 -67 0 -90z m-10 -279 c-2 -29 -3 -8
-3 47 0 55 1 79 3 53 2 -26 2 -71 0 -100z m-10 -385 c-2 -37 -3 -9 -3 62 0 72
1 102 3 68 2 -34 2 -93 0 -130z m-10 -560 c-1 -60 -3 -11 -3 107 0 118 2 167
3 108 2 -60 2 -156 0 -215z"/>
<path d="M7934 8982 c-518 -531 -1923 -1938 -2525 -2529 -557 -546 -599 -591
-599 -644 0 -18 54 -19 1760 -19 l1759 0 3 418 c4 532 -7 1455 -22 1817 -18
472 -64 1252 -73 1261 -2 2 -138 -135 -303 -304z"/>
<path d="M9709 4553 l-106 -4 -7 -82 c-24 -314 -30 -474 -30 -872 -1 -247 3
-512 8 -589 l8 -138 50 48 c85 83 318 344 419 470 238 295 440 604 616 941 74
142 76 146 60 172 -21 34 -46 38 -352 45 -432 11 -557 12 -666 9z"/>
</g>
</svg>"""

# -------------------------------------------------------------------
# PROPIEDADES
# -------------------------------------------------------------------

class HERBIE_MaterialDensityItem(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material,
        description="Material a procesar"
    )
    density: bpy.props.FloatProperty(
        name="Densidad",
        default=40.0,
        min=0.001,
        description="Tamaño (Cube Size) para este material"
    )

class HERBIE_Properties(bpy.types.PropertyGroup):
    pack_margin: bpy.props.FloatProperty(
        name="Pack Margin",
        description="Margen entre islas al empacar",
        default=0.03,
        min=0.0,
        max=1.0,
        precision=3
    )
    
    show_material_colors: bpy.props.BoolProperty(
        name="Mostrar Colores por Material",
        description="Dibuja colores aleatorios por material en el UV Editor",
        default=False
    )
    
    mapping_type: bpy.props.EnumProperty(
        name="Método",
        description="Tipo de proyección a aplicar",
        items=[
            ('CUBE', "Cube Projection", ""),
            ('CYLINDER', "Cylinder Projection", ""),
            ('SPHERE', "Sphere Projection", ""),
            ('VIEW', "Project from View", ""),
            ('VIEW_BOUNDS', "Project from View (Bounds)", "")
        ],
        default='CUBE'
    )
    
    cube_size: bpy.props.FloatProperty(name="Cube Size", default=1.0, min=0.001)
    cyl_radius: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.001)
    correct_aspect: bpy.props.BoolProperty(name="Correct Aspect", default=True)
    scale_to_bounds: bpy.props.BoolProperty(name="Scale to Bounds", default=False)

    density_list: bpy.props.CollectionProperty(type=HERBIE_MaterialDensityItem)
    density_list_idx: bpy.props.IntProperty()


# -------------------------------------------------------------------
# INTERFAZ (PANELES)
# -------------------------------------------------------------------

class HERBIE_PT_Panel(bpy.types.Panel):
    bl_label = "Herbie"
    bl_idname = "HERBIE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Herbie'

    def draw_header(self, context):
        layout = self.layout
        global custom_icons
        # Si la imagen existe, dibuja el icono personalizado, de lo contrario un icono nativo.
        if custom_icons and "f4_logo" in custom_icons:
            layout.label(text="", icon_value=custom_icons["f4_logo"].icon_id)
        else:
            layout.label(text="", icon='VIEW_PAN')

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        layout.label(text="Proyección Rápida:")
        layout.prop(props, "mapping_type")
        
        box = layout.box()
        if props.mapping_type == 'CUBE':
            box.prop(props, "cube_size")
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'CYLINDER':
            box.prop(props, "cyl_radius")
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'SPHERE':
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'VIEW':
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'VIEW_BOUNDS':
            box.prop(props, "correct_aspect")
            
        layout.operator("uv.herbie_apply_mapping", text="Aplicar Proyección", icon='MOD_UVPROJECT')
        layout.separator()
        layout.operator("uv.herbie_select_top_faces", text="Seleccionar Caras Z (Top/Bottom)", icon='TRIA_UP_BAR')
        layout.separator()
        layout.separator()

        layout.label(text="Organización por Material:")
        layout.prop(props, "pack_margin")
        layout.operator("uv.herbie_organize", text="Organizar UVs por Material", icon='UV_ISLANDSEL')
        layout.prop(props, "show_material_colors", text="Color Random por Material", toggle=True)


class HERBIE_UL_DensityList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.6)
        split.prop(item, "material", text="", icon='MATERIAL')
        split.prop(item, "density", text="")


class HERBIE_PT_DensitiesPanel(bpy.types.Panel):
    bl_label = "Densidades"
    bl_idname = "HERBIE_PT_DensitiesPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Herbie'
    bl_parent_id = "HERBIE_PT_Panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        row = layout.row()
        row.template_list("HERBIE_UL_DensityList", "", props, "density_list", props, "density_list_idx", rows=4)
        
        col = row.column(align=True)
        col.operator("uv.herbie_density_add", text="", icon='ADD')
        col.operator("uv.herbie_density_remove", text="", icon='REMOVE')

        layout.separator()
        layout.operator("uv.herbie_apply_densities", text="Aplicar Densidades", icon='FILE_TICK')


# -------------------------------------------------------------------
# OPERADORES
# -------------------------------------------------------------------

class HERBIE_OT_SelectTopFaces(bpy.types.Operator):
    bl_idname = "uv.herbie_select_top_faces"
    bl_label = "Seleccionar Caras Top/Bottom"
    bl_description = "Selecciona las caras que apuntan hacia arriba y abajo (eje Z local) para facilitar rotación de UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
            
        bpy.ops.mesh.select_mode(type="FACE")
        
        bm = bmesh.from_edit_mesh(obj.data)
        
        for face in bm.faces:
            face.select = (abs(face.normal.z) > 0.707)
            
        bmesh.update_edit_mesh(obj.data)
        
        self.report({'INFO'}, "Caras superiores e inferiores seleccionadas")
        return {'FINISHED'}


class HERBIE_OT_DensityAdd(bpy.types.Operator):
    bl_idname = "uv.herbie_density_add"
    bl_label = "Añadir Material"
    
    def execute(self, context):
        context.scene.herbie_props.density_list.add()
        return {'FINISHED'}


class HERBIE_OT_DensityRemove(bpy.types.Operator):
    bl_idname = "uv.herbie_density_remove"
    bl_label = "Remover Material"
    
    def execute(self, context):
        props = context.scene.herbie_props
        idx = props.density_list_idx
        if len(props.density_list) > 0:
            props.density_list.remove(idx)
            if idx > 0:
                props.density_list_idx = idx - 1
        return {'FINISHED'}


class HERBIE_OT_ApplyDensities(bpy.types.Operator):
    bl_idname = "uv.herbie_apply_densities"
    bl_label = "Aplicar Densidades de Material"
    bl_description = "Aplica un Cube Projection a las caras de cada material en la lista con su densidad configurada"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.herbie_props
        
        if not props.density_list:
            self.report({'WARNING'}, "La lista de densidades está vacía.")
            return {'CANCELLED'}
            
        initial_mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="FACE")
        
        bm = bmesh.from_edit_mesh(obj.data)
        
        processed_count = 0
        
        for item in props.density_list:
            mat = item.material
            if not mat:
                continue
                
            mat_idx = -1
            for i, slot_mat in enumerate(obj.data.materials):
                if slot_mat == mat:
                    mat_idx = i
                    break
                    
            if mat_idx == -1:
                continue 
                
            for face in bm.faces:
                face.select = (face.material_index == mat_idx)
            bmesh.update_edit_mesh(obj.data)
            
            try:
                bpy.ops.uv.cube_project(cube_size=item.density)
                processed_count += 1
            except Exception as e:
                self.report({'ERROR'}, f"Fallo en material {mat.name}: {e}")
                
            for face in bm.faces:
                face.select = False
            bmesh.update_edit_mesh(obj.data)
            
        bpy.ops.object.mode_set(mode=initial_mode)
        
        self.report({'INFO'}, f"Densidades aplicadas a {processed_count} materiales encontrados.")
        return {'FINISHED'}


class HERBIE_OT_ApplyMapping(bpy.types.Operator):
    bl_idname = "uv.herbie_apply_mapping"
    bl_label = "Aplicar Proyección (HERBIE)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        props = context.scene.herbie_props
        initial_mode = context.active_object.mode
        
        if initial_mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_all(action='SELECT')
        
        try:
            if props.mapping_type == 'CUBE':
                bpy.ops.uv.cube_project(cube_size=props.cube_size, correct_aspect=props.correct_aspect, scale_to_bounds=props.scale_to_bounds)
            elif props.mapping_type == 'CYLINDER':
                bpy.ops.uv.cylinder_project(radius=props.cyl_radius, correct_aspect=props.correct_aspect, scale_to_bounds=props.scale_to_bounds)
            elif props.mapping_type == 'SPHERE':
                bpy.ops.uv.sphere_project(correct_aspect=props.correct_aspect, scale_to_bounds=props.scale_to_bounds)
            elif props.mapping_type == 'VIEW':
                bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=props.correct_aspect, scale_to_bounds=props.scale_to_bounds)
            elif props.mapping_type == 'VIEW_BOUNDS':
                bpy.ops.uv.project_from_view(camera_bounds=False, correct_aspect=props.correct_aspect, scale_to_bounds=True)
        except Exception as e:
            self.report({'ERROR'}, f"Fallo al aplicar proyección: {e}")
            return {'CANCELLED'}
            
        if initial_mode == 'OBJECT':
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            
        return {'FINISHED'}


class HERBIE_OT_OrganizeUVs(bpy.types.Operator):
    bl_idname = "uv.herbie_organize"
    bl_label = "Organizar UVs (HERBIE)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.herbie_props
        
        original_sync = context.scene.tool_settings.use_uv_select_sync
        context.scene.tool_settings.use_uv_select_sync = False
        
        bpy.ops.object.mode_set(mode='OBJECT')
        used_materials = set()
        for poly in obj.data.polygons:
            if poly.material_index < len(obj.material_slots):
                used_materials.add(poly.material_index)
                
        if not used_materials:
            context.scene.tool_settings.use_uv_select_sync = original_sync
            return {'CANCELLED'}

        sorted_active_materials = sorted(list(used_materials))

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        for face in bm.faces:
            face.select = True
        bmesh.update_edit_mesh(obj.data)
        
        bpy.ops.uv.cube_project()

        uv_area = None
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                uv_area = area
                break

        restructure_area = False
        if uv_area is None:
            context.area.type = 'IMAGE_EDITOR'
            uv_area = context.area
            restructure_area = True

        uv_region = [r for r in uv_area.regions if r.type == 'WINDOW'][0]
        offset_step = 1.1

        for position_index, mat_idx in enumerate(sorted_active_materials, start=1):
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                face.select = (face.material_index == mat_idx)
            bmesh.update_edit_mesh(obj.data)

            override = {
                'window': context.window,
                'screen': context.screen,
                'area': uv_area,
                'region': uv_region,
                'scene': context.scene,
                'active_object': obj,
                'edit_object': obj,
                'selectable_objects': [obj],
                'selected_objects': [obj],
            }

            try:
                if hasattr(context, "temp_override"):
                    with context.temp_override(**override):
                        bpy.ops.uv.select_all(action='SELECT') 
                        bpy.ops.uv.pack_islands(margin=props.pack_margin, scale=True, rotate=False)
                else:
                    bpy.ops.uv.select_all(override, action='SELECT')
                    bpy.ops.uv.pack_islands(override, margin=props.pack_margin, scale=True, rotate=False)
            except Exception as e:
                pass

            move_x = offset_step * position_index
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[uv_layer].uv.x += move_x

            bmesh.update_edit_mesh(obj.data)

        if restructure_area:
            context.area.type = 'VIEW_3D'

        bm = bmesh.from_edit_mesh(obj.data)
        for face in bm.faces:
            face.select = False
        bmesh.update_edit_mesh(obj.data)

        context.scene.tool_settings.use_uv_select_sync = original_sync
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {'FINISHED'}


def draw_uv_colors():
    context = bpy.context
    if not hasattr(context.scene, "herbie_props") or not context.scene.herbie_props.show_material_colors:
        return
    obj = context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return
    area = context.area
    if not area or area.type != 'IMAGE_EDITOR':
        return

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        return

    coords = []
    colors = []

    def get_color(idx):
        random.seed(idx + 100)
        return (random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), 0.4)

    for face in bm.faces:
        mat_idx = face.material_index
        col = get_color(mat_idx)
        
        loops = face.loops
        if len(loops) >= 3:
            uv0 = loops[0][uv_layer].uv
            for i in range(1, len(loops) - 1):
                coords.append((uv0.x, uv0.y))
                coords.append((loops[i][uv_layer].uv.x, loops[i][uv_layer].uv.y))
                coords.append((loops[i+1][uv_layer].uv.x, loops[i+1][uv_layer].uv.y))
                
                colors.append(col)
                colors.append(col)
                colors.append(col)

    if not coords:
        return

    try:
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    except ValueError:
        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "color": colors})
    
    gpu.state.blend_set('ALPHA')
    shader.bind()
    batch.draw(shader)
    gpu.state.blend_set('NONE')


# -------------------------------------------------------------------
# REGISTRO
# -------------------------------------------------------------------

# Código Base64 del logo de los 4 Fantásticos
logo_base64 = b"""
iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAD8UlEQVR4nO2d23LbMBBD1538/y+7Dx3N2KwV87IXgMR5TlosAFG0FEtmQgghhBBCCCGEEEKI/XlUC8jg+Xw+Z3/38Xhs7dF2w62E3ctOpaAfJCPwbzAXglI4Quh3sJWBSixy8C0sRaAQyRR8C3oRoMUxB9+CWgRIUTsF34JWBCgxkcHPGI+mJwIIEWa+Zkeay6KzW0O1ALN1UyuNZNZuVlwAdvNeYZ2F7shBCv0OptlKzJwxiCH4FoY5/2T+Z2YcpniB9snjE6nGjg6HFvyI/lY76uxpKwCqAb1kb/KyVoIUk1eOHAS8T1tIfoSvAEjDzhBxJI7MGb0ShBZA4d+DUoKwAij87yCUIKQACr+f6hKkXwd45fTwLyp9cC9Ar4EK/51eP7w1uhZA4a9RUQK3Aih8H7JLkLoHUPh9ZPrkUgBEE3tg1X3hoT9tBUA7+tHDp7kZ1GOkwp+jx7fVWUqvA1TAEn4WSwVgO/oZw49eBUJXAIXvQ6SP0wVgMpRJ6yyzM4atAChH/y7hR/k5VQAWU1l0ejEz77afAk4Lf5aQAlQv/7uGH+HrcAHQzUXXF83o/O4rAPMXNRnw9nebPcAJ4UewRQEU/jxDBUA0GlFTNSOeuK4A2ef/U8P39Jn2FHBq+N5QFkDh+0FXAIXvS3cBEIxH0MBCr1duK0D0BlDhv+PlN8UpQOHHAV8AhR8LdAEUfjywBVD4OUAWQOHnAVcAhZ8LVAEUfj4wBVD4NUAUQOHXUV4AhV9LaQEUfj1lBVD4GKQ/I2j0Z8Vn0p8R5HX3SeHn0JtX6ilA4eMB+74AkcOP9z+ooP+x4gPdY+IuFH4OZU8Krf7Wr+hjJKfyK4GiFhXgcFQAMrz3WcMF0D4Am9F8tAIQEfEpSwU4nKkC6DSAyUwuWgFIiLrItnQkfxO120oxEoL37FFew7w5VNwT6eNSATJeaHA60Y/k1x7gcJYLoFUgjowXcugPQkDJ8sulALvt9lnw8F1/EwhIpk/pzwhSCX6n1x/IZwSpBGtkh29W+Lh4leCdivDN9N1ACCp9KH9lzOklqLy/YAby2rhTS1AdvhnQm0NPKwFC+GYJewCV4H9QwjdL2gSOlmDXIozOlnGFNe1TwOgwu5VgdJ6sy+upHwNnSsBehJkZaL8c2sPMcKwlmNGdfWON7iWPDHcemWajfscvUhlYZ4EwkNU8M27tZiAFMPM9z0eayqKzW0O1gFciN3tom0+E8M3ACnDBuuvvASX4CygxLTsVAS34C0hRLcxFQA3+AlpcC1MR0IO/oBDZglwEluAvqMR+AqEMbKG/Qiv8joxCMAfess0gv7FSip3CFkIIIYQQQgghhBAH8xcZfsANFw2V8AAAAABJRU5ErkJggg==
"""
classes = (
    HERBIE_MaterialDensityItem,
    HERBIE_Properties,
    HERBIE_UL_DensityList,
    HERBIE_PT_Panel,
    HERBIE_PT_DensitiesPanel,
    HERBIE_OT_SelectTopFaces,
    HERBIE_OT_DensityAdd,
    HERBIE_OT_DensityRemove,
    HERBIE_OT_ApplyDensities,
    HERBIE_OT_ApplyMapping,
    HERBIE_OT_OrganizeUVs
)

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    
    svg_path = os.path.join(tempfile.gettempdir(), "f4_logo.svg")
    try:
        with open(svg_path, 'w') as f:
            f.write(SVG_DATA)
        custom_icons.load("f4_logo", svg_path, 'IMAGE')
    except Exception as e:
        print("Error al cargar el icono SVG:", e)

    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.herbie_props = bpy.props.PointerProperty(type=HERBIE_Properties)
    
    global _herbie_draw_handler
    _herbie_draw_handler = bpy.types.SpaceImageEditor.draw_handler_add(draw_uv_colors, (), 'WINDOW', 'POST_VIEW')
def unregister():
    global custom_icons
    if custom_icons is not None:
        bpy.utils.previews.remove(custom_icons)
        custom_icons = None

    global _herbie_draw_handler
    if _herbie_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_herbie_draw_handler, 'WINDOW')
        _herbie_draw_handler = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.herbie_props

if __name__ == "__main__":
    register()