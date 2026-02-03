#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试模板API"""

import requests
import json

# 测试 API
url = 'http://localhost:8001/api/template/list'

try:
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API 返回成功!")
        print(f"总数: {data['total']}")
        print(f"模板数量: {len(data['templates'])}")
        
        # 按 module_type 统计
        from collections import Counter
        types = Counter([t['module_type'] for t in data['templates']])
        print("\n模板分布:")
        for t, count in types.items():
            print(f"  {t}: {count} 个")
        
        # 显示前3个模板
        print("\n前3个模板:")
        for t in data['templates'][:3]:
            print(f"  - {t['name']} ({t['module_type']})")
    else:
        print(f"❌ API 返回错误: {response.text}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
