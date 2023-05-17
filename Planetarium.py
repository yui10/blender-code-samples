import csv
import math
import pathlib
from urllib import request
import time
import bpy
import os
import sqlite3
import numpy as np


class Color:
    BLACK = (0.0, 0.0, 0.0)
    WHITE = (1.0, 1.0, 1.0)
    RED = (1.0, 0.0, 0.0)
    #透過付き
    BLACK_T = (0.0, 0.0, 0.0, 1.0)
    WHITE_T = (1.0, 1.0, 1.0, 1.0)
    RED_T = (1.0, 0.0, 0.0, 1.0)

    # hexをrgbへ変換する
    def hex_to_rgb(hex: str, max=1, Trans=-1):
        const = max / 255
        hex = hex.strip().strip("#")
        color = [int(hex[i:i + 2], 16) * const for i in range(0, len(hex), 2)]
        if 0 <= Trans <= 1: color.append(Trans)
        return tuple(color)


def create_color_materials(color: tuple | str):
    if type(color) is str:
        color = Color.hex_to_rgb(color, Trans=1)
    material = bpy.data.materials.new("Color")
    material.diffuse_color = color
    return material


def create_color_emission_materials(color: tuple | str):
    if type(color) is str:
        color = Color.hex_to_rgb(color, Trans=1)
    material = bpy.data.materials.new("Color")
    material.diffuse_color = color
    material.use_nodes = True
    material.node_tree.nodes.clear()
    mix = material.node_tree.nodes.new('ShaderNodeMixShader')
    emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
    trans = material.node_tree.nodes.new(type="ShaderNodeBsdfTranslucent")
    node_output = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    material.node_tree.links.new(trans.outputs[0], mix.inputs[1])
    material.node_tree.links.new(emission.outputs[0], mix.inputs[2])
    material.node_tree.links.new(mix.outputs[0], node_output.inputs[0])
    material.node_tree.nodes[0].inputs[0].default_value = 0.5
    material.node_tree.nodes[1].inputs[0].default_value = color
    material.node_tree.nodes[1].inputs[1].default_value = 1
    return material


def add_text(text: str,
             color=(0, 0, 0, 1),
             location_=(0, 0, 0),
             scale_=(0, 0, 0),
             rotation_=(0, 0, 0)):
    bpy.ops.object.text_add(location=location_,
                            scale=scale_,
                            rotation=rotation_)
    _object = bpy.context.object
    _object.data.body = text
    _object.data.align_x = "CENTER"
    _object.data.align_y = "CENTER"

    material = create_color_materials(color)
    _object.data.materials.append(material)
    _object.active_material.diffuse_color = color
    return _object


def Load_CSV(csv_name: str, base="hip"):
    """
    恒星データのダウンロードおよび読み取りを行う
    """
    csv_path = base_path / csv_name
    if not csv_path.exists():  #csvがなければダウンロード
        url = f"http://astro.starfree.jp/commons/{base}/{csv_name}"
        print(f"Download : {url}")
        request.urlretrieve(url=url, filename=str(csv_path))

    with open(str(csv_path)) as f:
        reader = csv.reader(f)
        return [row for row in reader]


def trans_hip_base(item: list):
    """
    基礎データを変換 (フォーマット: hip番号,x,y,z,lon,lat,サイズ,色)
    """
    ra = math.radians(trans_lon_coordinate(item[1:4]) % 360)  #赤経
    dec = math.radians(trans_lat_coordinate(item[5:8]) % 360)  #赤緯
    if item[4] == "0":
        dec = -dec
    x, y, z = (100 * math.cos(ra) * math.cos(dec),
               100 * math.sin(ra) * math.cos(dec), 100 * math.sin(dec))
    grade = max(0.3 - float(item[8]) / 20, 0)
    return [int(item[0]), x, y, z, ra, dec, grade, 0]


def trans_hip_line(item: list):
    """
    星座線恒星データを変換 (フォーマット: hip番号,x,y,z,lon,lat,サイズ,色)
    """
    ra = math.radians(trans_lon_coordinate(item[1:4]) % 360)  #赤経
    dec = math.radians(trans_lat_coordinate(item[4:7]) % 360)  #赤緯
    x, y, z = (100 * math.cos(ra) * math.cos(dec),
               100 * math.sin(ra) * math.cos(dec), 100 * math.sin(dec))
    grade = max(0.3 - float(item[7]) / 20, 0)
    return [
        int(item[0]), x, y, z, ra, dec, grade,
        color_ref.get(item[13][0], 0)
    ]


def trans_lon_coordinate(item: list | tuple):  #時分秒リスト
    return (int(item[0]) * 15 + int(item[1]) / 4 + float(item[2]) / 240)


def trans_lat_coordinate(item: list | tuple):  #度分秒リスト
    return (int(item[0]) + int(item[1]) / 60 + float(item[2]) / 3600)


#0~360->-180~180
# def Trans_NormalAngle180(angle: int | float | list | tuple, radians=False):
#     if type(angle) in [int, float]:
#         if radians:
#             angle = math.radians(angle)
#         angle = (angle + 180) % 360 - 180
#         return (angle + 360) if angle < -180 else angle
#     angle_lists_result = []
#     for item in angle:
#         if radians:
#             item = math.radians(item)
#         item = (item + 180) % 360 - 180
#         angle_lists_result.append(item + 360 if item < -180 else item)
#     return angle_lists_result


def create_line_cube(A: tuple, B: tuple, size: float, degree=False, div=10):
    AA_360, BB_360 = np.array(A), np.array(B)
    if degree:
        AA_360, BB_360 = np.deg2rad(AA_360), np.deg2rad(BB_360)

    ra_np = np.linspace(AA_360[0], BB_360[0], num=div)
    dec_np = np.linspace(AA_360[1], BB_360[1], num=div)

    verts_tmp = [[] for i in range(4)]
    for i in range(div):
        ra, dec = ra_np[i], dec_np[i]
        x_t, y_t, z_t = math.cos(ra) * math.cos(dec), math.sin(ra) * math.cos(
            dec), math.sin(dec)

        x, y, z = (-size / 2 + 100.5 * x_t, -size / 2 + 100.5 * y_t,
                   -size / 2 + 100.5 * z_t)
        verts_tmp[0].append((x, y, z))

        x, y, z = (size / 2 + 100.5 * x_t, size / 2 + 100.5 * y_t,
                   -size / 2 + 100.5 * z_t)
        verts_tmp[1].append((x, y, z))

        x, y, z = (-size / 2 + 100.5 * x_t, -size / 2 + 100.5 * y_t,
                   size / 2 + 100.5 * z_t)

        verts_tmp[2].append((x, y, z))

        x, y, z = (size / 2 + 100.5 * x_t, size / 2 + 100.5 * y_t,
                   size / 2 + 100.5 * z_t)
        verts_tmp[3].append((x, y, z))

    verts = verts_tmp[0] + verts_tmp[1] + verts_tmp[2] + verts_tmp[3]

    faces = []
    for i in range(div - 1):
        faces.append((i, i + 1, div + i + 1, div + i))
        faces.append(
            (div * 2 + i, div * 2 + i + 1, div * 3 + i + 1, div * 3 + i))
        faces.append((i, i + 1, div * 2 + i + 1, div * 2 + i))
        faces.append((div + i, div + i + 1, div * 3 + i + 1, div * 3 + i))

    #メッシュを定義する
    mesh = bpy.data.meshes.new("Plane_mesh")
    #頂点と面のデータからメッシュを生成する
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)

    #メッシュのデータからオブジェクトを定義する
    obj = bpy.data.objects.new("Plane", mesh)
    #オブジェクトの生成場所をカーソルに指定する
    obj.location = bpy.context.scene.cursor.location
    #オブジェクトをシーンにリンク(表示)させる
    bpy.context.scene.collection.objects.link(obj)
    return obj


def Calculate_xyz(ra: float, dec: float, distance: float | int):
    """
    緯度経度からx,y,zの3次元座標に変換する
    """
    x, y, z = (distance * math.cos(ra) * math.cos(dec),
               distance * math.sin(ra) * math.cos(dec),
               distance * math.sin(dec))
    return (x, y, z)


#-----------以上関数定義終了------------------
total_time = time.time()
desk_path = pathlib.Path('~/Desktop').expanduser()
base_path = desk_path / "Planetarium"
if not base_path.exists():
    os.mkdir(base_path)
print(bpy.data.texts[__file__[1:]].filepath)
__file__ = bpy.data.texts[__file__[1:]].filepath

#全てのオブジェクトを削除
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(True)

screen_size = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "2160p": (3840, 2160)
}
#レンダリングの設定
scene = bpy.context.scene
scene.render.engine = 'CYCLES'  #レンダリングエンジンを Cycles に変更
scene.render.resolution_x, scene.render.resolution_y = screen_size["1080p"]
scene.render.resolution_percentage = 100  #レンダリングする画像サイズの百分率
bpy.context.scene.render.use_multiview = True  #レンダーのマルチビューをオンにする

#ワールドの背景色を変更
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[
    0].default_value = Color.hex_to_rgb("000119", Trans=1)

#カメラの設定
bpy.ops.object.camera_add()
camera = bpy.data.objects['カメラ']
camera.location = (0, 0, 1.6)
camera.rotation_euler = (math.pi / 2, 0, 0)
camera.data.type = 'PANO'  #カメラのレンズをパノラマ状に設定
camera.data.cycles.panorama_type = 'EQUIRECTANGULAR'  #タイプを正距円筒図に設定
scene.camera = camera

#カメラのクリッピング設定
bpy.context.object.data.clip_start = 0.1  #カメラのクリッピング開始位置
bpy.context.object.data.clip_end = 150  #カメラのクリッピング終了位置
bpy.context.object.data.stereo.use_spherical_stereo = True  #カメラの立体視の球状ステレオをONにする

#光源
bpy.ops.object.light_add(
    type='SUN',
    location=(0, 0, 10),
    rotation=(0, 0, 0),
)
bpy.context.object.data.energy = 0.001
bpy.context.object.data.color = Color.hex_to_rgb("000a10")

#恒星の色を定義
color_ref = {"": 0, "O": 1, "B": 2, "A": 3, "F": 4, "G": 5, "K": 6, "M": 7}
colors = [(0.5, 0.5, 0.5, 1), (0.3, 0.3, 0.8, 1), (0.3, 0.3, 0.8, 1),
          (0.5, 0.5, 1, 1), (1, 1, 1, 1), (0.8, 0.8, 0.4, 1), (0.8, 0.4, 0, 1),
          (0.4, 0, 0, 1)]
color_materials = []
for color in colors:
    material = create_color_emission_materials(color)
    material.node_tree.nodes[1].inputs[1].default_value = 10
    color_materials.append(material)

sqlite_path = base_path / "star_data.db"
is_create = not sqlite_path.exists()

try:
    start = time.time()
    connect = sqlite3.connect(str(sqlite_path))
    cursor = connect.cursor()
    star_list = []  #星の情報を格納
    if is_create:  # If the *.db file does not exist, the creation process is performed.
        # create table to SQlite
        cursor.execute(
            "Create Table star_base(id INTEGER PRIMARY KEY, hip INTEGER, x REAL, y REAL, z REAL, lon REAL, lat REAL, size REAL, color INTEGER)"
        )
        cursor.execute(
            "Create Table star_line(id INTEGER PRIMARY KEY,name TEXT, hip1 INTEGER, hip2 INTEGER)"
        )
        cursor.execute(
            "Create Table star_line_name(id INTEGER PRIMARY KEY,id_star INTEGER,name TEXT,scientific TEXT,name_jp TEXT)"
        )
        cursor.execute(
            "Create Table star_line_pos(id INTEGER PRIMARY KEY,id_star INTEGER,lon_h INTEGER,lon_m INTEGER,lat INTEGER)"
        )
        connect.commit()

        # load csv data
        # 星座
        # http://astro.starfree.jp/commons/hip/
        # 星座 略符一覧
        # https://www.nao.ac.jp/new-info/constellation2.html
        #星座に使われる星
        line_star_csv_data = Load_CSV("hip_constellation_line_star.csv")
        line_csv_data = Load_CSV("hip_constellation_line.csv")  #星座線
        line_name_csv_data = Load_CSV("constellation_name_utf8.csv",
                                      base="constellation")  #星座の名前
        line_pos_csv_data = Load_CSV("position.csv",
                                     base="constellation")  #星座の位置
        major_csv_data = Load_CSV("hip_lite_major.csv")  #厳選されたその他の恒星

        line_hip_list = [i[0] for i in line_star_csv_data]  #重複データのリスト
        for item in major_csv_data:
            if not item[0] in line_hip_list:
                star_list.append(trans_hip_base(item))
        for item in line_star_csv_data:
            star_list.append(trans_hip_line(item))
        print("Trance Ready")
        #Insert to SQlite
        sql_insert = "Insert into star_base(hip, x, y, z, lon, lat, size, color) values (?,?,?,?,?,?,?,?)"
        cursor.executemany(sql_insert, star_list)
        connect.commit()
        sql_insert_line = "Insert into star_line(name,hip1, hip2) values (?,?,?)"
        cursor.executemany(sql_insert_line, line_csv_data)
        sql_insert_line_name = "Insert into star_line_name(id_star,name,scientific,name_jp) values (?,?,?,?)"
        cursor.executemany(sql_insert_line_name, line_name_csv_data)
        sql_insert_line_pos = "Insert into star_line_pos(id_star,lon_h,lon_m,lat) values (?,?,?,?)"
        cursor.executemany(sql_insert_line_pos, line_pos_csv_data)
        connect.commit()

    #Load SQLite
    sql_select = 'SELECT hip, x, y, z, size, color FROM star_base;'
    star_list = [row for row in cursor.execute(sql_select)]

    sql_select_constellation = 'SELECT * FROM star_line_name as name INNER JOIN star_line_pos as pos ON name.id_star=pos.id_star;'
    star_line_constellation = [
        row for row in cursor.execute(sql_select_constellation)
    ]

    sql_select_line = 'SELECT h1.lon,h1.lat,h1.z,h1.size ,h2.lon,h2.lat,h2.z,h2.size FROM star_line as line INNER JOIN star_base as h1 ON line.hip1=h1.hip INNER JOIN star_base as h2 ON line.hip2=h2.hip Where line.name=?;'

    #0:h1_xyz,1:h1_size,2:h2_xyz,3:h2_size
    star_line_list = []
    for name in star_line_constellation:
        data = [[
            tuple(row[0:2]), row[2], row[3],
            tuple(row[4:6]), row[6], row[7]
        ] for row in cursor.execute(sql_select_line, (name[2], ))]
        star_line_list.append((name[2], data))

    print(f"CSV load and SQL insert time : {time.time()-start}")
except:
    raise
finally:
    cursor.close()
    connect.close()

print(f"star_size:{len(star_list)}")
print(f"star_line size :{len(star_line_list)}")

start = time.time()
animation_color = create_color_emission_materials(colors[0])
animation_color_obj = animation_color.node_tree.nodes[0].inputs[0]
animation_color_obj.default_value = 0
animation_color_obj.keyframe_insert(data_path="default_value", frame=1)
animation_color_obj.default_value = 1
animation_color_obj.keyframe_insert(data_path="default_value", frame=48)

#星座線の生成
for name, data in star_line_list:
    obj_list = []
    for item in data:
        # if item[1] < 0 and item[4] < 0:
        #     continue
        obj = create_line_cube(item[0], item[3], 0.1, div=2)
        if obj is not None:
            obj.active_material = animation_color
            obj_list.append(obj)
    ob = bpy.context.view_layer.objects.active
    ob.select_set(False)
    for obj in obj_list:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    if len(data) > 1:
        bpy.ops.object.join()
    for obj in bpy.context.selected_objects:
        obj.name = name
        obj.data.name = name

print(f"create star line time : {time.time() - start}")

start = time.time()
#日本語を扱うためにフォントを変更
font = bpy.data.fonts.load("C:\\Windows\\Fonts\\meiryob.ttc")
#アニメーションの設定
text_animation_color = create_color_emission_materials(Color.RED_T)
text_animation_color_obj = text_animation_color.node_tree.nodes[0].inputs[0]
text_animation_color_obj.default_value = 0
text_animation_color_obj.keyframe_insert(data_path="default_value", frame=1)
text_animation_color_obj.default_value = 1
text_animation_color_obj.keyframe_insert(data_path="default_value", frame=48)
#星座名を表示させる
for data in star_line_constellation:
    ra = math.radians(trans_lon_coordinate((data[7], data[8], 0)) % 360)  #赤経
    dec = math.radians(trans_lat_coordinate((data[9], 0, 0)) % 360)  #赤緯
    l = Calculate_xyz(ra, dec, 99)
    # if l[2] >= 0:
    text = add_text(f"{data[4]}\n{data[3]}",
                    location_=l,
                    rotation_=(math.atan(l[2] / 100) + math.pi / 2, 0,
                               math.atan2(l[1], l[0]) - math.pi / 2))
    text.scale = (3, 3, 3)
    text.active_material = text_animation_color
    text.name = f"text_{data[2]}"
    text.data.font = font

print(f"create star line name time : {time.time() - start}")

#恒星を生成
start = time.time()
for item in range(len(star_list)):
    if item % 100 == 0:
        print(item)
    star = star_list[item]
    bpy.ops.mesh.primitive_uv_sphere_add(location=(star[1], star[2], star[3]),
                                         scale=(star[4], star[4], star[4]))
    obj = bpy.context.object
    obj.active_material = color_materials[star[5]]
print(f"create star time : {time.time() - start}")

#レンダーのビューフォーマットのステレオ 3D 設定
bpy.context.scene.render.image_settings.views_format = 'STEREO_3D'
#レンダーのビューフォーマットをトップボトムに設定(立体視用に上下に出力)
bpy.context.scene.render.image_settings.stereo_3d_format.display_mode = 'TOPBOTTOM'
#アニメーションの設定
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = 48

bpy.context.scene.render.image_settings.file_format = 'FFMPEG'  #ファイル形式を設定
bpy.context.scene.render.ffmpeg.format = 'MPEG4'  #コンテナの設定
bpy.context.scene.render.filepath = str(base_path / "planetarium.mp4")
print(f"total time:{time.time() - total_time}")