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

_herbie_draw_handler = None
custom_icons = None

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
    
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else bpy.utils.user_resource('SCRIPTS', path="addons")
    icon_path = os.path.join(script_dir, "f4_logo.png")
    
    if os.path.exists(icon_path):
        custom_icons.load("f4_logo", icon_path, 'IMAGE')

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