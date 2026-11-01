# SPDX-FileCopyrightText: 2026 HonoriusAD395
# SPDX-License-Identifier: MIT
# AI-Generated: 本文件由 AI 编码助手生成/修改，经人工审核。详见 NOTICE 文件。
#               This file was produced with AI assistance; see NOTICE.

"""
头像管理器
负责从资源文件夹、.pak 文件中加载单位头像
"""

import os
import struct
import zipfile
from typing import Dict, Optional
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication


class PortraitManager:
    """
    管理单位头像资源
    
    扫描三个位置（优先级 1 > 2 > 3）：
    1. resource/interface/scene/portrait_squad/（直接文件夹）
    2. resource/interface/interface.pak -> interface/scene/portrait_squad/
    3. resource/interface.pak -> interface/scene/portrait_squad/
    
    图片命名：{unit_name}_00.{jpg,png,bmp,tga}
    """
    
    def __init__(self):
        self.resource_path = ""
        self._cache: Dict[str, QPixmap] = {}  # {unit_name: QPixmap}
    
    def load_folder(self, path: str):
        """
        加载资源文件夹，按优先级扫描并缓存头像
        
        Args:
            path: 用户选择的资源根目录
        """
        self.resource_path = path
        # 不清空旧缓存，仅覆盖同名文件
        
        if not path or not os.path.isdir(path):
            return
        
        # 按优先级 3→2→1 处理（低优先先写入，高优先覆盖）
        # 3. resource/interface.pak
        self._load_from_pak(
            os.path.join(path, "resource", "interface.pak"),
            "interface/scene/portrait_squad/"
        )
        
        # 2. resource/interface/interface.pak
        self._load_from_pak(
            os.path.join(path, "resource", "interface", "interface.pak"),
            "scene/portrait_squad/"
        )
        
        # 1. resource/interface/scene/portrait_squad/（直接文件夹，最高优先级）
        self._load_from_folder(
            os.path.join(path, "resource", "interface", "scene", "portrait_squad")
        )
    
    def get_portrait(self, unit_name: str) -> Optional[QPixmap]:
        """获取单位头像，没有则返回 None"""
        return self._cache.get(unit_name)
    
    def _load_from_folder(self, folder_path: str):
        """扫描直接文件夹中的头像文件"""
        if not os.path.isdir(folder_path):
            return
        
        for fname in os.listdir(folder_path):
            QApplication.processEvents()
            if fname.lower().endswith('.tga'):
                self._try_cache_image(fname, lambda fn=fname: self._load_tga_file(os.path.join(folder_path, fn)))
            else:
                self._try_cache_image(fname, lambda fn=fname: QPixmap(os.path.join(folder_path, fn)))
    
    def _load_from_pak(self, pak_path: str, prefix: str):
        """从 .pak（zip）文件中读取头像"""
        if not os.path.isfile(pak_path):
            return
        
        try:
            with zipfile.ZipFile(pak_path, 'r') as z:
                for name in z.namelist():
                    QApplication.processEvents()
                    if not name.startswith(prefix):
                        continue
                    rel = name[len(prefix):]
                    self._try_cache_image(rel, lambda n=name, zf=z: self._load_pixmap_from_zip(zf, n))
        except Exception:
            pass
    
    def _try_cache_image(self, fname: str, loader):
        """尝试解析文件名并缓存头像
        
        文件名格式：{unit_name}_00.{jpg,png,bmp,tga}
        """
        # 检查扩展名
        lower = fname.lower()
        if not (lower.endswith('_00.jpg') or lower.endswith('_00.png') or
                lower.endswith('_00.bmp') or lower.endswith('_00.tga')):
            return
        
        # 提取单位名：去掉末尾 _00.xxx
        dot_idx = fname.rfind('.')
        if dot_idx < 0:
            return
        name_no_ext = fname[:dot_idx]
        if not name_no_ext.endswith('_00'):
            return
        unit_name = name_no_ext[:-3]  # 去掉 _00
        
        if not unit_name:
            return
        
        pixmap = loader()
        if pixmap and not pixmap.isNull():
            self._cache[unit_name] = pixmap
    
    def _load_pixmap_from_zip(self, zf: zipfile.ZipFile, name: str) -> QPixmap:
        """从 zip 文件中加载图片"""
        try:
            data = zf.read(name)
            if name.lower().endswith('.tga'):
                return self._tga_to_pixmap(data)
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            return pixmap
        except Exception:
            return QPixmap()
    
    def _load_tga_file(self, path: str) -> QPixmap:
        """加载 TGA 文件"""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            return self._tga_to_pixmap(data)
        except Exception:
            return QPixmap()
    
    def _tga_to_pixmap(self, data: bytes) -> QPixmap:
        """
        将 TGA 数据解码为 QPixmap
        
        支持类型：
        - 类型 2: 未压缩真彩色 (BGR/BGRA)
        - 类型 10: RLE 压缩真彩色
        """
        if len(data) < 18:
            return QPixmap()
        
        # 解析 TGA 头 (18 字节)
        # 偏移: 0=ID长度, 1=调色板类型, 2=图像类型, 3-7=调色板信息
        # 8-9=X原点, 10-11=Y原点, 12-13=宽度, 14-15=高度
        # 16=像素深度, 17=描述符 (bit5: 0=bottom-left, 1=top-left)
        img_type = data[2]
        width = struct.unpack('<H', data[12:14])[0]
        height = struct.unpack('<H', data[14:16])[0]
        depth = data[16]
        origin_top = (data[17] & 0x20) != 0
        
        if width == 0 or height == 0 or width > 4096 or height > 4096:
            return QPixmap()
        
        # 跳过 ID 字段
        id_length = data[0]
        pixel_offset = 18 + id_length
        
        # 如果是调色板类型，跳过调色板
        if data[1] != 0:
            palette_entries = struct.unpack('<H', data[5:7])[0]
            palette_entry_size = data[7]
            pixel_offset += palette_entries * (palette_entry_size // 8)
        
        pixel_data = data[pixel_offset:]
        
        if img_type == 2:
            img = self._decode_uncompressed_tga(pixel_data, width, height, depth, origin_top)
        elif img_type == 10:
            img = self._decode_rle_tga(pixel_data, width, height, depth, origin_top)
        else:
            return QPixmap()
        
        return QPixmap.fromImage(img) if img else QPixmap()
    
    def _decode_uncompressed_tga(self, data: bytes, width: int, height: int,
                                  depth: int, origin_top: bool = False) -> QImage:
        """解码未压缩 TGA (类型 2) — 统一转 32-bit ARGB，用 slice 写入"""
        img = QImage(width, height, QImage.Format_ARGB32)
        bpl = width * 4
        src = 0
        
        for y in range(height):
            dst_y = y if origin_top else (height - 1 - y)
            row_buf = bytearray(bpl)
            
            if depth == 32:
                row = data[src:src + width * 4]
                row_buf[:len(row)] = row
                src += width * 4
            elif depth == 24:
                for x in range(min(width, (len(data) - src) // 3)):
                    b = data[src]; g = data[src + 1]; r = data[src + 2]
                    off = x * 4
                    row_buf[off] = b
                    row_buf[off + 1] = g
                    row_buf[off + 2] = r
                    row_buf[off + 3] = 255
                    src += 3
            else:
                return QImage()
            
            ptr = img.scanLine(dst_y)
            ptr.setsize(bpl)
            ptr[:bpl] = bytes(row_buf)
        
        return img
    
    def _decode_rle_tga(self, data: bytes, width: int, height: int,
                        depth: int, origin_top: bool = False) -> QImage:
        """解码 RLE 压缩 TGA (类型 10) — 先解压为原始像素再转换"""
        bpp = depth // 8
        expected_pixels = width * height
        raw = bytearray(expected_pixels * bpp)
        
        src = 0
        dst = 0
        while dst < expected_pixels * bpp and src < len(data):
            packet = data[src]
            src += 1
            is_rle = (packet & 0x80) != 0
            count = (packet & 0x7F) + 1
            
            if is_rle:
                if src + bpp - 1 >= len(data):
                    break
                pixel = data[src:src + bpp]
                src += bpp
                for _ in range(min(count, (expected_pixels * bpp - dst) // bpp)):
                    raw[dst:dst + bpp] = pixel
                    dst += bpp
            else:
                copy_len = min(count * bpp, len(data) - src, expected_pixels * bpp - dst)
                raw[dst:dst + copy_len] = data[src:src + copy_len]
                dst += copy_len
                src += copy_len
        
        # 截取实际写入的数据
        raw = raw[:dst]
        return self._decode_uncompressed_tga(bytes(raw), width, height, depth)
