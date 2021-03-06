import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Matrix, Quaternion
import math 
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from datetime import datetime 
import random 
from math import cos
from math import degrees
from math import radians
from math import sin
from math import sqrt 

from . import collisionmatoperators

def get_all_vertexs(vert_data):
    vertexs = [] 
    
    for vert in vert_data.text.split(" " * 5):
        data = vert.split(",")
        
        try:
            x = float(data[0])
            y = float(data[1])
            z = float(data[2])
            
            vertexs.append(Vector((x, y, z)))
        except:
            a = 0
    
    return vertexs 

######################## STOLEN FROM GIZZ (edited) ###########################
def get_closest_axis_point(axis, center, points):

    closest     = None
    closestDist = math.inf

    for p in points:
        
        rel  = (p - center).normalized()
        dist = (rel - axis).length

        if dist < closestDist:
            closest     = p
            closestDist = dist

    return closest

def create_box(polyline, allverts, materials):
    
    #get box verts
    idxs = []
    idxs.append(int(polyline.attrib["v1"]))
    idxs.append(int(polyline.attrib["v2"]))
    idxs.append(int(polyline.attrib["v3"]))
    idxs.append(int(polyline.attrib["v4"]))
    verts = []
    for idx in idxs:
        verts.append(allverts[idx])
    
    p1 = verts[0]
    p2 = verts[1]
    p3 = verts[2]
    p4 = verts[3]

    a, b, c, d = p1, p2, p3, p4

    cf1 = (a + b) / 2
    cf2 = (c + d) / 2
    cf3 = (a + d) / 2
    cf4 = (b + c) / 2
    cf5 = (a + c) / 2
    cf6 = (b + d) / 2

    # caclulate box center
    center = (cf3 + cf4) / 2

    rightest = get_closest_axis_point(Vector((1, 0, 0)), center, [cf1, cf2, cf3, cf4, cf5, cf6])
    upest    = get_closest_axis_point(Vector((0, 0, 1)), center, [cf1, cf2, cf3, cf4, cf5, cf6])
    right    = (rightest - center).normalized()
    up       = (upest    - center).normalized()
    forward  = Vector.cross(right, up).normalized()

    mat = Matrix.Identity(4)

    mat[0] = (right.x,   right.y,   right.z,   0)
    mat[1] = (up.x,      up.y,      up.z,      0)
    mat[2] = (forward.x, forward.y, forward.z, 0)
    mat[3] = (0,         0,         0,         1)

    mat.normalize()

    rotation = mat.to_quaternion().inverted().normalized().to_euler('XYZ')

    # calculate scale
    seq = [cf1, cf2, cf3, cf4, cf5, cf6]

    _cf1 = get_closest_axis_point(right,    center, seq)
    _cf2 = get_closest_axis_point(-right,   center, seq)
    _cf3 = get_closest_axis_point(-up,      center, seq)
    _cf4 = get_closest_axis_point(up,       center, seq)
    _cf5 = get_closest_axis_point(-forward, center, seq)
    _cf6 = get_closest_axis_point(forward,  center, seq)

    W = (_cf2 - _cf1).length
    L = (_cf3 - _cf4).length
    H = (_cf5 - _cf6).length

    scale = Vector((W, L, H))

    # blender stuff
    mesh = bpy.data.meshes.new("box")
    bm   = bmesh.new()

    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()

    materialindex = int(polyline.attrib["m"]) - 1
    mat = materials[materialindex]
    
    mesh.materials.append(mat)

    obj = bpy.data.objects.new("box", mesh)

    #obj.data.materials.append(material)

    obj.location                = center
    obj.rotation_euler          = rotation
    obj.scale                   = scale
    obj.sollumtype = "Bound Box"
    
    return obj
#######################################################################

def create_triangle(triangleline, vertices, materials):
    
    indicies = []
    indicies.append(int(triangleline.attrib["v1"]))
    indicies.append(int(triangleline.attrib["v2"]))
    indicies.append(int(triangleline.attrib["v3"]))
    return indicies
    verts = []
    for i in indicies:
        verts.append(vertices[i])
        
    #create mesh
    mesh = bpy.data.meshes.new("Geometry")
    mesh.from_pydata(verts, [], [[0, 1, 2]]) 
    
    materialindex = int(triangleline.attrib["m"]) - 1 
    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Triangle", mesh)
    obj.sollumtype = "Bound Triangle"

    return obj
    
def create_sphere(sphereline, vertices, materials):
    
    radius = float(sphereline.attrib["radius"])
    location = vertices[int(sphereline.attrib["v"])]
    materialindex = int(sphereline.attrib["m"]) - 1
    
    mesh = bpy.data.meshes.new("sphere")
    bm   = bmesh.new()

    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=radius * 2)
    bm.to_mesh(mesh)
    bm.free()
    
    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("sphere", mesh)
    obj.sollumtype = "Bound Sphere"
    obj.location = location
    
    return obj

def create_capsule_mesh(l, r):
    
    length = l
    radius = r
    rings = 9
    segments = 16

    topRings = []
    bottomRings = []
    topCap = []
    bottomCap = []

    vertId = 0

    for j in range(0, rings + 1):

        if j == rings:
            
            topVertex = Vector((0, 0, ((length / 2) + radius)))
            bottomVertex = Vector((0, 0, -((length / 2) + radius)))

            topCap.append(topVertex)
            bottomCap.append(bottomVertex)
        else:

            heightAngle = radians((90 / rings) * (j + 1))

            topRing = []
            bottomRing = []

            for i in range(0, segments):

                zAngle = radians((360 / segments) * i)

                x = radius * cos(zAngle) * sin(heightAngle)
                y = radius * sin(zAngle) * sin(heightAngle)
                z = radius * cos(heightAngle)

                topVertex = Vector((x, y, z + (length / 2)))
                bottomVertex = Vector((x, y, -(z + (length / 2))))

                topRing.append(vertId)
                bottomRing.append(vertId + ((rings * segments) + 1))
                topCap.append(topVertex)
                bottomCap.append(bottomVertex)

                vertId += 1

            topRings.append(topRing)
            bottomRings.append(bottomRing)

    verts = topCap + bottomCap

    faces = []

    ringIndex = len(topRings) - 1
    while ringIndex > 0:
        
        topRing = topRings[ringIndex]
        topNextRing = topRings[ringIndex - 1]

        bottomRing = bottomRings[ringIndex]
        bottomNextRing = bottomRings[ringIndex - 1]
        
        for i in range(0, segments):

            index1 = i
            index2 = 0 if i + 1 == segments else i + 1

            topCapFace = [topRing[index1], topRing[index2], topNextRing[index2], topNextRing[index1]]
            bottomCapFace = [bottomRing[index2], bottomRing[index1], bottomNextRing[index1], bottomNextRing[index2]]
            faces.append(topCapFace)
            faces.append(bottomCapFace)

        ringIndex -= 1

    topRing = topRings[rings - 1]
    bottomRing = bottomRings[rings - 1]

    topCapRing = topRings[0]
    bottomCapRing = bottomRings[0]

    topCapFaces = []
    bottomCapFaces = []

    for i in range(0, segments):
        
        index1 = i
        index2 = 0 if i + 1 == segments else i + 1

        bodyFace = [topRing[index2], topRing[index1], bottomRing[index1], bottomRing[index2]]
        topCapFace = [topCapRing[index1], topCapRing[index2], rings * segments]
        bottomCapFace = [bottomCapRing[index2], bottomCapRing[index1], ((rings * segments) * 2) + 1]

        faces.append(bodyFace)
        topCapFaces.append(topCapFace)
        bottomCapFaces.append(bottomCapFace)

    faces += topCapFaces + bottomCapFaces

    mesh = bpy.data.meshes.new(name="Capsule")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    mesh = bpy.data.meshes.new(name="Capsule")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    return mesh
    
    #return object_data_add(context, mesh, operator=None)

def get_distance_of_verts(a, b):
    locx = b[0] - a[0]
    locy = b[1] - a[1]
    locz = b[2] - a[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2) 
    return distance

def get_direction_of_verts(a, b):
    direction  = (a - b).normalized()
    axis_align = Vector((0.0, 0.0, 1.0))

    angle = axis_align.angle(direction)
    axis  = axis_align.cross(direction)

    q = Quaternion(axis, angle)
    
    return q.to_euler('XYZ')

def create_capsule(capsuleline, vertices, materials):
    #obj.sollumtype = "Bound Capsule"
    
    materialindex = int(capsuleline.attrib["m"])
    radius = float(capsuleline.attrib["radius"])
    v1 = vertices[int(capsuleline.attrib["v1"])]
    v2 = vertices[int(capsuleline.attrib["v2"])]
    length = get_distance_of_verts(v1, v2)    
    rot = get_direction_of_verts(v1, v2)
    
    mesh = create_capsule_mesh(length, radius)
    
    mesh.materials.append(materials[materialindex])
    
    obj = bpy.data.objects.new("Capsule", mesh)
    
    obj.location = (v1 + v2) / 2     
    obj.rotation_euler = rot
    
    return obj

def create_cylinder(cylinderline, vertices, materials):
    #obj.sollumtype = "Bound Cylinder"
    return None

## NOT USED ## at least codewalker doesnt use it?
def create_disc(discline, vertices, materials):
    #obj.sollumtype = "Bound Disc"
    return None

def create_materials(emats):
    mats = []
    
    for emat in emats:
        matindex = str(emat.find("Type").attrib["value"])
        mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
        mats.append(mat)
        
    return mats
        
def read_bounds(name, bounds):
    
    type = bounds.attrib["type"]
    
    cobj = None
    
    if(type == "Composite"):
        cobj = bpy.data.objects.new(name, None)
        
    if(cobj == None):
        return #log error 
    
    #read children 
    for child in bounds.find("Children"):
        #read materials
        materials = create_materials(child.find("Materials"))   
        
        bobj = bpy.data.objects.new("GeometryBVH", None)
        
        geocenter = child.find("GeometryCenter")
        location = Vector((float(geocenter.attrib["x"]), float(geocenter.attrib["y"]), float(geocenter.attrib["z"])))
        
        bobj.location = location
        
        vertices = get_all_vertexs(child.find("Vertices"))  
        
        indicies = []
        tverts = vertices
        
        polys = []
        
        for p in child.find("Polygons"):
            if(p.tag == "Triangle"):
                indicies.append(create_triangle(p, vertices, materials))
                #way to slow for the plugin...
                t = None#create_triangle(p, vertices, materials)
                if( t!= None):
                    t.parent = bobj
                    bpy.context.scene.collection.objects.link(t)
            if(p.tag == "Box"):
                b = create_box(p, vertices, materials)
                if(b != None):
                    polys.append(b)
                    #b.parent = bobj
                    bpy.context.scene.collection.objects.link(b)
            if(p.tag == "Sphere"):
                s = create_sphere(p, vertices, materials)
                if(s != None):
                    polys.append(s)
                    #s.parent = bobj
                    bpy.context.scene.collection.objects.link(s)
            if(p.tag == "Capsule"):
                c = create_capsule(p, vertices, materials)
                if(c != None):
                    polys.append(c)
                    #c.parent = bobj
                    bpy.context.scene.collection.objects.link(c)
            if(p.tag == "Cylinder"):
                c = create_cylinder(p, vertices, materials)
                if(c != None):
                    polys.append(c)
                    #c.parent = bobj
                    bpy.context.scene.collection.objects.link(c)
            if(p.tag == "Disc"):
                d = create_disc(p, vertices, materials)
                if(d != None):
                    polys.append(d)
                    #d.parent = bobj
                    bpy.context.scene.collection.objects.link(d)
        
        mesh = bpy.data.meshes.new("Geometry")
        mesh.from_pydata(vertices, [], indicies)
        bobj = bpy.data.objects.new("GeometryBVH", mesh)  
        for poly in polys:
            poly.parent = bobj
        
        bobj.parent = cobj
        bpy.context.scene.collection.objects.link(bobj)
        
        #clean up old verts
        #bobj.select_set(True)
        #bpy.ops.object.mode_set(mode='EDIT')
        #bpy.ops.mesh.select_loose()
        #bpy.ops.mesh.delete(type='VERT')
        
    return cobj

def read_ybn_xml(context, filepath, root):
    
    filename = os.path.basename(filepath[:-8]) 
    
    objs = []
    
    for bound in root.findall("Bounds"):
        objs.append(read_bounds(filename, bound)) 
    
    return objs 

class ImportYbnXml(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ybn"

    # ImportHelper mixin class uses this
    filename_ext = ".ybn.xml"

    def execute(self, context):
        tree = ET.parse(self.filepath)
        root = tree.getroot() 
        
        objs = read_ybn_xml(context, self.filepath, root) 

        for obj in objs:
            context.scene.collection.objects.link(obj)

        return {'FINISHED'}
    
# Only needed if you want to add into a dynamic menu
def menu_func_import_ybn(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Ybn (.ybn.xml)")

def register():
    bpy.utils.register_class(ImportYbnXml)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ybn)
    print("registering ybnimport")


def unregister():
    bpy.utils.unregister_class(ImportYbnXml)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ybn)
