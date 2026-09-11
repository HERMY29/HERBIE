bl_info = {
    "name": "HERBIE - UV Organizer",
    "author": "HERBIE Dev",
    "version": (1, 15),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > H.E.R.B.I.E",
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
import tempfile

_herbie_draw_handler = None
custom_icons = None

SVG_DATA = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010904//EN"
 "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg version="1.0" xmlns="http://www.w3.org/2000/svg"
 width="1280.000000pt" height="1280.000000pt" viewBox="0 0 1280.000000 1280.000000"
 preserveAspectRatio="xMidYMid meet">
<g transform="translate(0.000000,1280.000000) scale(0.100000,-0.100000)" fill="#ffffff" stroke="none">
<path d="M5685 12793 c-634 -85 -1203 -234 -1790 -470 -440 -177 -1111 -595 -1584 -986 -1293 -1070 -2044 -2463 -2291 -4249 -18 -131 -20 -200 -20 -597 0 -330 4 -489 15 -602 151 -1502 719 -2766 1749 -3888 182 -198 264 -276 463 -434 867 -691 1752 -1134 2708 -1356 1032 -239 2155 -200 3300 114 355 98 487 151 905 361 741 372 1325 793 1855 1335 451 463 778 926 1079 1529 340 683 553 1411 678 2320 20 143 23 206 23 480 0 330 -10 464 -60 860 -63 485 -109 686 -265 1145 -642 1884 -1793 3183 -3455 3898 -532 229 -1118 397 -1771 507 l-234 40 -637 -1 c-351 -1 -651 -4 -668 -6z m930 -983 c1053 -64 1936 -342 2722 -857 568 -372 1098 -909 1521 -1541 259 -387 434 -705 516 -937 603 -1715 512 -3259 -274 -4630 -283 -492 -627 -926 -1105 -1393 -233 -228 -293 -276 -535 -437 -819 -544 -1632 -851 -2510 -950 -195 -22 -680 -31 -896 -16 -669 47 -1476 251 -1973 501 -1719 861 -2746 2279 -3050 4210 -38 245 -36 771 4 1182 181 1811 1103 3222 2755 4216 346 208 990 447 1527 566 250 56 369 77 483 85 159 12 624 12 815 1z"/>
<path d="M5900 11219 c-309 -19 -977 -200 -1387 -375 -806 -344 -1450 -841 -1954 -1509 -272 -360 -529 -826 -653 -1184 -551 -1589 -378 -3064 519 -4416 195 -295 283 -404 489 -610 763 -761 1577 -1224 2470 -1405 850 -173 1758 -84 2733 268 l182 65 6 41 c13 96 23 1022 15 1431 -9 431 -25 879 -36 961 l-5 42 -187 8 c-103 5 -945 9 -1872 9 -1540 0 -2262 -8 -2841 -31 l-156 -6 -7 23 c-13 42 -19 440 -8 533 l10 89 1994 1996 c2310 2313 3439 3450 3446 3470 2 5 -21 29 -50 55 -39 34 -89 62 -194 106 -556 234 -1080 368 -1664 425 -192 19 -656 27 -850 14z"/>
<path d="M9563 8538 c5 -1247 18 -2174 32 -2243 2 -11 4 -129 4 -262 l1 -243 478 0 c456 0 1030 14 1041 26 28 27 51 762 32 1014 -36 482 -125 901 -284 1325 -217 584 -588 1163 -1047 1639 -103 106 -125 125 -131 109 -6 -14 -8 -13 -8 9 -1 35 -44 68 -89 68 l-35 0 6 -1442z m114 1210 c-2 -18 -4 -6 -4 27 0 33 2 48 4 33 2 -15 2 -42 0 -60z m-10 -180 c-2 -18 -4 -6 -4 27 0 33 2 48 4 33 2 -15 2 -42 0 -60z m-10 -185 c-2 -21 -4 -6 -4 32 0 39 2 55 4 38 2 -18 2 -50 0 -70z m-10 -220 c-2 -21 -4 -4 -4 37 0 41 2 58 4 38 2 -21 2 -55 0 -75z m-10 -210 c-2 -21 -4 -6 -4 32 0 39 2 55 4 38 2 -18 2 -50 0 -70z m-10 -276 c-2 -23 -3 -1 -3 48 0 50 1 68 3 42 2 -26 2 -67 0 -90z m-10 -279 c-2 -29 -3 -8 -3 47 0 55 1 79 3 53 2 -26 2 -71 0 -100z m-10 -385 c-2 -37 -3 -9 -3 62 0 72 1 102 3 68 2 -34 2 -93 0 -130z m-10 -560 c-1 -60 -3 -11 -3 107 0 118 2 167 3 108 2 -60 2 -156 0 -215z"/>
<path d="M7934 8982 c-518 -531 -1923 -1938 -2525 -2529 -557 -546 -599 -591 -599 -644 0 -18 54 -19 1760 -19 l1759 0 3 418 c4 532 -7 1455 -22 1817 -18 472 -64 1252 -73 1261 -2 2 -138 -135 -303 -304z"/>
<path d="M9709 4553 l-106 -4 -7 -82 c-24 -314 -30 -474 -30 -872 -1 -247 3 -512 8 -589 l8 -138 50 48 c85 83 318 344 419 470 238 295 440 604 616 941 74 142 76 146 60 172 -21 34 -46 38 -352 45 -432 11 -557 12 -666 9z"/>
</g>
</svg>"""

# -------------------------------------------------------------------
# ACTUALIZACIÓN EN VIVO (MR FANTASTIC)
# -------------------------------------------------------------------

def update_fantastic_percs(self, context):
    """Callback que asegura que los porcentajes no pasen del 100% y sea individual por objeto."""
    if 'prev_fantastic_percs' not in self:
        self['prev_fantastic_percs'] = [0.0] * 32
        
    prev = self['prev_fantastic_percs']
    curr = list(self.fantastic_percs)
    
    changed_idx = -1
    for i in range(32):
        if abs(curr[i] - prev[i]) > 0.0001:
            changed_idx = i
            break
            
    if changed_idx != -1:
        total_others = sum(curr) - curr[changed_idx]
        if total_others + curr[changed_idx] > 100.0:
            allowed = max(0.0, 100.0 - total_others)
            # Prevenir recursión infinita
            if abs(self.fantastic_percs[changed_idx] - allowed) > 0.0001:
                self.fantastic_percs[changed_idx] = allowed
                curr[changed_idx] = allowed
        
        self['prev_fantastic_percs'] = [float(x) for x in curr]

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

class HERBIE_MaterialKeepItem(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material,
        description="Material a no borrar"
    )

class HERBIE_Properties(bpy.types.PropertyGroup):
    pack_margin: bpy.props.FloatProperty(
        name="Pack Margin",
        description="Margen entre islas al empacar",
        default=0.003,
        min=0.0,
        max=1.0,
        precision=4
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
    
    keep_list: bpy.props.CollectionProperty(type=HERBIE_MaterialKeepItem)
    keep_list_idx: bpy.props.IntProperty()
    
    master_material: bpy.props.PointerProperty(
        name="Material principal",
        type=bpy.types.Material,
        description="Material maestro que reemplazará a todos los que no estén en la lista"
    )

    fantastic_margin: bpy.props.FloatProperty(
        name="Margen Mr Fantastic",
        description="Margen entre las islas de UV al empacar con Mr Fantastic",
        default=0.003,
        min=0.0,
        max=1.0,
        precision=4
    )

# -------------------------------------------------------------------
# LISTAS (UILists)
# -------------------------------------------------------------------
class HERBIE_UL_FantasticList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        slot = item
        split = layout.split(factor=0.6)
        
        if slot.material:
            split.label(text=slot.name, icon='MATERIAL')
            if index < 32:
                # Agrupamos la propiedad y el símbolo % en una misma fila alineada
                row = split.row(align=True)
                row.prop(data, "fantastic_percs", index=index, text="")
                row.label(text="%")
            else:
                split.label(text="Límite: 32 mats")
        else:
            split.label(text="Vacío", icon='MATERIAL')
            
class HERBIE_UL_DensityList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.15)
        split.label(text=f"{index + 1}.")
        row = split.row(align=True)
        row.prop(item, "material", text="")
        row.prop(item, "density", text="")

class HERBIE_UL_KeepList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.15)
        split.label(text=f"{index + 1}.")
        row = split.row(align=True)
        row.prop(item, "material", text="")

# -------------------------------------------------------------------
# PANELES 
# -------------------------------------------------------------------

class HERBIE_PT_Panel(bpy.types.Panel):
    bl_label = ""
    bl_idname = "HERBIE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'H.E.R.B.I.E'

    def draw_header(self, context):
        layout = self.layout
        global custom_icons
        if custom_icons and "f4_logo" in custom_icons:
            layout.label(text=" H.E.R.B.I.E", icon_value=custom_icons["f4_logo"].icon_id)
        else:
            layout.label(text=" H.E.R.B.I.E", icon='VIEW_PAN')

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        layout.label(text="Mapas de Bake:")
        layout.operator("uv.herbie_prepare_bake_map", text="Preparar Mapa para Bake", icon='RENDER_STILL')
        layout.operator("uv.herbie_keep_uvmap_001", text="Conservar solo UVMap.001", icon='X')
        layout.separator()

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
        
        layout.label(text="Edición:")
        layout.operator("uv.herbie_select_top_faces", text="Seleccionar Caras Z (Top/Bottom)", icon='TRIA_UP_BAR')
        layout.operator("mesh.herbie_count_islands", text="Contar Mallas Seleccionadas", icon='MESH_DATA')
        layout.separator()

        layout.label(text="Organización por Material:")
        layout.prop(props, "pack_margin")
        layout.operator("uv.herbie_organize", text="Organizar UVs por Material", icon='UV_ISLANDSEL')
        layout.prop(props, "show_material_colors", text="Color Random por Material", toggle=True)

class HERBIE_PT_DensitiesPanel(bpy.types.Panel):
    bl_label = "Densidades"
    bl_idname = "HERBIE_PT_DensitiesPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'H.E.R.B.I.E'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        row = layout.row()
        row.template_list("HERBIE_UL_DensityList", "", props, "density_list", props, "density_list_idx", rows=4)
        
        col = row.column(align=True)
        col.operator("uv.herbie_density_add", text="", icon='ADD')
        col.operator("uv.herbie_density_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("uv.herbie_density_move", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("uv.herbie_density_move", text="", icon='TRIA_DOWN').direction = 'DOWN'

        layout.separator()
        layout.operator("uv.herbie_apply_densities", text="Aplicar Densidades", icon='FILE_TICK')

class HERBIE_PT_FantasticPanel(bpy.types.Panel):
    bl_label = "Mr Fantastic"
    bl_idname = "HERBIE_PT_FantasticPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'H.E.R.B.I.E'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props
        obj = context.active_object

        if obj and obj.type == 'MESH':
            # La lista se actualiza automáticamente directo desde el objeto
            layout.template_list("HERBIE_UL_FantasticList", "", obj, "material_slots", obj, "active_material_index", rows=5)
        else:
            layout.label(text="Selecciona un objeto.")

        layout.separator()
        layout.prop(props, "fantastic_margin")
        layout.separator()
        layout.operator("uv.herbie_fantastic_generate", text="Generar UVs", icon='TEXTURE')

class HERBIE_PT_KeepPanel(bpy.types.Panel):
    bl_label = "Procesador de modelo"
    bl_idname = "HERBIE_PT_KeepPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'H.E.R.B.I.E'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        if not props.master_material:
            layout.prop(props, "master_material", text="Material principal")
        else:
            layout.prop(props, "master_material", text="")
            
        layout.separator()

        row = layout.row()
        row.template_list("HERBIE_UL_KeepList", "", props, "keep_list", props, "keep_list_idx", rows=4)
        
        col = row.column(align=True)
        col.operator("uv.herbie_keep_add", text="", icon='ADD')
        col.operator("uv.herbie_keep_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("uv.herbie_keep_move", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("uv.herbie_keep_move", text="", icon='TRIA_DOWN').direction = 'DOWN'

        layout.separator()
        layout.operator("uv.herbie_clear_bake_materials", text="Borrar Materiales de Bake", icon='TRASH')

# -------------------------------------------------------------------
# OPERADORES
# -------------------------------------------------------------------

class HERBIE_OT_FantasticGenerate(bpy.types.Operator):
    bl_idname = "uv.herbie_fantastic_generate"
    bl_label = "Generar UVs Fantastic"
    bl_description = "Acomoda las UVs respetando porcentajes, maximizando el espacio sin estirar"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.herbie_props
        
        active_items = []
        for i, slot in enumerate(obj.material_slots):
            if i >= 32: break
            perc = obj.fantastic_percs[i]
            if perc > 0 and slot.material:
                active_items.append((i, perc))
                
        if not active_items:
            self.report({'WARNING'}, "No hay porcentajes asignados.")
            return {'CANCELLED'}

        original_sync = context.scene.tool_settings.use_uv_select_sync
        context.scene.tool_settings.use_uv_select_sync = False
        
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
        override = {
            'window': context.window, 'screen': context.screen,
            'area': uv_area, 'region': uv_region, 'scene': context.scene,
            'active_object': obj, 'edit_object': obj,
            'selectable_objects': [obj], 'selected_objects': [obj]
        }

        rects = {}
        rem_x, rem_y, rem_w, rem_h = 0.0, 0.0, 1.0, 1.0
        remaining_perc = sum(perc for _, perc in active_items)
        
        sorted_items = sorted(active_items, key=lambda x: x[1], reverse=True)
        
        for mat_idx, perc in sorted_items:
            ratio = perc / remaining_perc if remaining_perc > 0 else 0
            if rem_w > rem_h:
                w = rem_w * ratio
                rects[mat_idx] = (rem_x, rem_y, max(0.001, w), max(0.001, rem_h))
                rem_x += w
                rem_w -= w
            else:
                h = rem_h * ratio
                rects[mat_idx] = (rem_x, rem_y, max(0.001, rem_w), max(0.001, h))
                rem_y += h
                rem_h -= h
            remaining_perc -= perc

        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
            
        bpy.ops.mesh.select_mode(type="FACE")

        for mat_idx, (x0, y0, w, h) in rects.items():
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            
            has_faces = False
            for face in bm.faces:
                face.select = (face.material_index == mat_idx)
                if face.select: has_faces = True
            
            bmesh.update_edit_mesh(obj.data)
            if not has_faces:
                continue

            try:
                if hasattr(context, "temp_override"):
                    with context.temp_override(**override):
                        bpy.ops.uv.select_all(action='SELECT')
                        bpy.ops.uv.pack_islands(margin=0.0, scale=True, rotate=True)
                else:
                    bpy.ops.uv.select_all(override, action='SELECT')
                    bpy.ops.uv.pack_islands(override, margin=0.0, scale=True, rotate=True)
            except Exception:
                pass

            bm = bmesh.from_edit_mesh(obj.data)
            for face in bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[uv_layer].uv.x *= (1.0 / w)
                        loop[uv_layer].uv.y *= (1.0 / h)
            bmesh.update_edit_mesh(obj.data)

            try:
                if hasattr(context, "temp_override"):
                    with context.temp_override(**override):
                        bpy.ops.uv.select_all(action='SELECT')
                        bpy.ops.uv.pack_islands(margin=props.fantastic_margin, scale=True, rotate=False)
                else:
                    bpy.ops.uv.select_all(override, action='SELECT')
                    bpy.ops.uv.pack_islands(override, margin=props.fantastic_margin, scale=True, rotate=False)
            except Exception:
                pass

            bm = bmesh.from_edit_mesh(obj.data)
            for face in bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[uv_layer].uv.x = (loop[uv_layer].uv.x * w) + x0
                        loop[uv_layer].uv.y = (loop[uv_layer].uv.y * h) + y0
            bmesh.update_edit_mesh(obj.data)

        bm = bmesh.from_edit_mesh(obj.data)
        for face in bm.faces:
            face.select = False
        bmesh.update_edit_mesh(obj.data)

        if restructure_area:
            context.area.type = 'VIEW_3D'

        context.scene.tool_settings.use_uv_select_sync = original_sync
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, "Mr Fantastic aplicado con éxito.")
        return {'FINISHED'}


class HERBIE_OT_PrepareBakeMap(bpy.types.Operator):
    bl_idname = "uv.herbie_prepare_bake_map"
    bl_label = "Preparar Mapa para Bake"
    bl_description = "Conserva solo el mapa activo de render, lo nombra 'UVMap' y crea 'UVMap.001' para editar"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool([obj for obj in context.selected_objects if obj.type == 'MESH'])

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        procesados = 0
        for obj in selected_objs:
            uvs = obj.data.uv_layers
            if not uvs:
                continue

            render_uv = None
            for uv in uvs:
                if uv.active_render:
                    render_uv = uv
                    break
            
            if not render_uv:
                render_uv = uvs.active

            to_remove = [uv.name for uv in uvs if uv.name != render_uv.name]
            for name in to_remove:
                uvs.remove(uvs[name])

            render_uv.name = "UVMap"
            render_uv.active_render = True

            new_uv_name = "UVMap.001"
            if new_uv_name not in uvs:
                new_uv = uvs.new(name=new_uv_name)
            else:
                new_uv = uvs[new_uv_name]

            new_uv.active = True
            procesados += 1

        self.report({'INFO'}, f"Mapa preparado para bake en {procesados} objetos.")
        return {'FINISHED'}


class HERBIE_OT_KeepUVMap001(bpy.types.Operator):
    bl_idname = "uv.herbie_keep_uvmap_001"
    bl_label = "Conservar solo UVMap.001"
    bl_description = "Borra todos los mapas de UV a excepción de UVMap.001 en los objetos seleccionados"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool([obj for obj in context.selected_objects if obj.type == 'MESH'])

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objs:
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        procesados = 0
        for obj in selected_objs:
            uvs = obj.data.uv_layers
            if "UVMap.001" not in uvs:
                continue
                
            to_remove = [uv.name for uv in uvs if uv.name != "UVMap.001"]
            for name in to_remove:
                uvs.remove(uvs[name])
                
            uvs["UVMap.001"].active = True
            uvs["UVMap.001"].active_render = True
            procesados += 1

        self.report({'INFO'}, f"Mapas limpios en {procesados} objetos. Solo UVMap.001 conservado.")
        return {'FINISHED'}


class HERBIE_OT_CountIslands(bpy.types.Operator):
    bl_idname = "mesh.herbie_count_islands"
    bl_label = "Contar Mallas Seleccionadas"
    bl_description = "Calcula cuántas mallas separadas (islas) tienes seleccionadas actualmente"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == 'EDIT'

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        
        faces = set(f for f in bm.faces if f.select)
        if not faces:
            self.report({'WARNING'}, "No hay geometría seleccionada para contar.")
            return {'CANCELLED'}
            
        islands = 0
        while faces:
            islands += 1
            stack = [faces.pop()]
            while stack:
                face = stack.pop()
                for edge in face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face in faces:
                            faces.remove(linked_face)
                            stack.append(linked_face)
                            
        self.report({'INFO'}, f"Mallas (Islas) seleccionadas: {islands}")
        return {'FINISHED'}


class HERBIE_OT_SelectTopFaces(bpy.types.Operator):
    bl_idname = "uv.herbie_select_top_faces"
    bl_label = "Seleccionar Caras Top/Bottom"
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

class HERBIE_OT_DensityMove(bpy.types.Operator):
    bl_idname = "uv.herbie_density_move"
    bl_label = "Mover Material"
    direction: bpy.props.EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])
    
    def execute(self, context):
        props = context.scene.herbie_props
        idx = props.density_list_idx
        lst = props.density_list
        if self.direction == 'UP' and idx > 0:
            lst.move(idx, idx - 1)
            props.density_list_idx -= 1
        elif self.direction == 'DOWN' and idx < len(lst) - 1:
            lst.move(idx, idx + 1)
            props.density_list_idx += 1
        return {'FINISHED'}


class HERBIE_OT_KeepAdd(bpy.types.Operator):
    bl_idname = "uv.herbie_keep_add"
    bl_label = "Añadir Material a Conservar"
    def execute(self, context):
        context.scene.herbie_props.keep_list.add()
        return {'FINISHED'}

class HERBIE_OT_KeepRemove(bpy.types.Operator):
    bl_idname = "uv.herbie_keep_remove"
    bl_label = "Remover Material"
    def execute(self, context):
        props = context.scene.herbie_props
        idx = props.keep_list_idx
        if len(props.keep_list) > 0:
            props.keep_list.remove(idx)
            if idx > 0:
                props.keep_list_idx = idx - 1
        return {'FINISHED'}

class HERBIE_OT_KeepMove(bpy.types.Operator):
    bl_idname = "uv.herbie_keep_move"
    bl_label = "Mover Material"
    direction: bpy.props.EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])
    
    def execute(self, context):
        props = context.scene.herbie_props
        idx = props.keep_list_idx
        lst = props.keep_list
        if self.direction == 'UP' and idx > 0:
            lst.move(idx, idx - 1)
            props.keep_list_idx -= 1
        elif self.direction == 'DOWN' and idx < len(lst) - 1:
            lst.move(idx, idx + 1)
            props.keep_list_idx += 1
        return {'FINISHED'}


class HERBIE_OT_ClearBakeMaterials(bpy.types.Operator):
    bl_idname = "uv.herbie_clear_bake_materials"
    bl_label = "Borrar materiales de bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        props = context.scene.herbie_props
        master_mat = props.master_material
        
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objs:
            self.report({'WARNING'}, "No hay objetos seleccionados.")
            return {'CANCELLED'}
            
        if not master_mat:
            self.report({'WARNING'}, "Asigna un Master Mat. primero.")
            return {'CANCELLED'}
        
        mats_to_keep_names = {item.material.name for item in props.keep_list if item.material}
        procesados = 0
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        original_active = context.view_layer.objects.active
        
        for obj in selected_objs:
            context.view_layer.objects.active = obj
            
            master_idx = -1
            for i, slot in enumerate(obj.material_slots):
                if slot.material == master_mat:
                    master_idx = i
                    break
            
            if master_idx == -1:
                obj.data.materials.append(master_mat)
                master_idx = len(obj.material_slots) - 1
                
            keep_indices = {master_idx}
            for i, slot in enumerate(obj.material_slots):
                if slot.material and slot.material.name in mats_to_keep_names:
                    keep_indices.add(i)
                    
            for poly in obj.data.polygons:
                if poly.material_index not in keep_indices:
                    poly.material_index = master_idx
                    
            used_indices = {poly.material_index for poly in obj.data.polygons}
            for i in range(len(obj.material_slots) - 1, -1, -1):
                if i not in used_indices:
                    obj.active_material_index = i
                    bpy.ops.object.material_slot_remove()
                    
            procesados += 1
            
        context.view_layer.objects.active = original_active
        self.report({'INFO'}, f"Procesador aplicado a {procesados} objetos.")
        return {'FINISHED'}


class HERBIE_OT_ApplyDensities(bpy.types.Operator):
    bl_idname = "uv.herbie_apply_densities"
    bl_label = "Aplicar Densidades de Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.herbie_props
        
        if not props.density_list:
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
            except Exception:
                pass
                
            for face in bm.faces:
                face.select = False
            bmesh.update_edit_mesh(obj.data)
            
        bpy.ops.object.mode_set(mode=initial_mode)
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
        except Exception:
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
            except Exception:
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

    try:
        bm = bmesh.from_edit_mesh(obj.data)
    except Exception:
        return

    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        return

    coords = []
    colors = []

    def get_color(idx):
        random.seed(idx + 100)
        return (random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), 0.5)

    loop_tris = bm.calc_loop_triangles()
    for tri in loop_tris:
        if tri[0].face.select:
            continue
            
        mat_idx = tri[0].face.material_index
        col = get_color(mat_idx)
        
        coords.append((tri[0][uv_layer].uv.x, tri[0][uv_layer].uv.y))
        coords.append((tri[1][uv_layer].uv.x, tri[1][uv_layer].uv.y))
        coords.append((tri[2][uv_layer].uv.x, tri[2][uv_layer].uv.y))
        
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

classes = (
    HERBIE_MaterialDensityItem,
    HERBIE_MaterialKeepItem,
    HERBIE_Properties,
    HERBIE_UL_FantasticList,
    HERBIE_UL_DensityList,
    HERBIE_UL_KeepList,
    HERBIE_PT_Panel,
    HERBIE_PT_FantasticPanel,
    HERBIE_PT_DensitiesPanel,
    HERBIE_PT_KeepPanel,
    HERBIE_OT_FantasticGenerate,
    HERBIE_OT_PrepareBakeMap,
    HERBIE_OT_KeepUVMap001,
    HERBIE_OT_SelectTopFaces,
    HERBIE_OT_CountIslands,
    HERBIE_OT_DensityAdd,
    HERBIE_OT_DensityRemove,
    HERBIE_OT_DensityMove,
    HERBIE_OT_KeepAdd,
    HERBIE_OT_KeepRemove,
    HERBIE_OT_KeepMove,
    HERBIE_OT_ClearBakeMaterials,
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

    # Añadimos la propiedad de porcentajes directamente en la clase Object
    bpy.types.Object.fantastic_percs = bpy.props.FloatVectorProperty(
        name="",
        size=32,
        min=0.0,
        max=100.0,
        update=update_fantastic_percs,
        description="Porcentaje del UV Grid a ocupar (independiente por objeto)"
    )

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
    del bpy.types.Object.fantastic_percs

if __name__ == "__main__":
    register()