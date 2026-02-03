#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试所有主要后端API端点
"""

import requests
import json
from typing import Dict, List

BASE_URL = 'http://localhost:8001'

def test_api(method: str, endpoint: str, description: str, data: dict = None) -> Dict:
    """测试单个API端点"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=5)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=5)
        else:
            return {'status': 'SKIP', 'message': f'不支持的方法: {method}'}
        
        if response.status_code == 200:
            return {'status': 'OK', 'code': response.status_code}
        elif response.status_code == 404:
            return {'status': 'NOT_FOUND', 'code': 404, 'message': '端点不存在'}
        elif response.status_code == 500:
            try:
                error_detail = response.json().get('detail', '未知错误')
            except:
                error_detail = response.text[:200]
            return {'status': 'ERROR', 'code': 500, 'message': error_detail}
        else:
            return {'status': 'WARN', 'code': response.status_code}
    except requests.exceptions.ConnectionError:
        return {'status': 'CONN_ERROR', 'message': '无法连接到后端'}
    except requests.exceptions.Timeout:
        return {'status': 'TIMEOUT', 'message': '请求超时'}
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}

def main():
    """主测试函数"""
    
    print("=" * 80)
    print("🔍 开始检测所有后端API端点")
    print("=" * 80)
    
    # 定义要测试的端点
    endpoints = [
        # 模板管理
        ('GET', '/api/template/list', '获取模板列表'),
        
        # AI模型管理
        ('GET', '/api/admin/ai-models/active', '获取激活的AI模型'),
        ('GET', '/api/admin/ai-models', '获取所有AI模型'),
        
        # 配置中心
        ('GET', '/api/admin/config-center/groups', '获取配置分组'),
        ('GET', '/api/admin/config-center/wechat', '获取微信配置'),
        ('GET', '/api/admin/config-center/roles', '获取角色列表'),
        ('GET', '/api/admin/config-center/users', '获取用户列表'),
        
        # 数据源管理
        ('GET', '/api/admin/datasources', '获取数据源列表'),
        
        # 客户管理
        ('GET', '/api/customers', '获取客户列表'),
        
        # 企业微信API（可能不存在）
        ('GET', '/api/wechat/work/users', '获取企业微信员工'),
        ('GET', '/api/wechat/work/groups', '获取企业微信群聊'),
        ('GET', '/api/wechat/official/users', '获取公众号用户'),
        
        # 基础端点
        ('GET', '/', '根路径'),
        ('GET', '/health', '健康检查'),
    ]
    
    results = {
        'OK': [],
        'NOT_FOUND': [],
        'ERROR': [],
        'WARN': [],
        'CONN_ERROR': [],
        'TIMEOUT': []
    }
    
    for method, endpoint, description in endpoints:
        result = test_api(method, endpoint, description)
        status = result['status']
        results[status].append({
            'endpoint': endpoint,
            'description': description,
            'result': result
        })
        
        # 打印结果
        status_emoji = {
            'OK': '✅',
            'NOT_FOUND': '❌',
            'ERROR': '🔴',
            'WARN': '⚠️',
            'CONN_ERROR': '🔌',
            'TIMEOUT': '⏱️'
        }
        
        emoji = status_emoji.get(status, '❓')
        print(f"{emoji} {method:4s} {endpoint:50s} - {description:30s}")
        
        if status in ['ERROR', 'WARN']:
            print(f"     错误: {result.get('message', '未知')[:100]}")
    
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    print(f"✅ 正常: {len(results['OK'])} 个")
    print(f"❌ 不存在: {len(results['NOT_FOUND'])} 个")
    print(f"🔴 错误: {len(results['ERROR'])} 个")
    print(f"⚠️  警告: {len(results['WARN'])} 个")
    print(f"🔌 连接失败: {len(results['CONN_ERROR'])} 个")
    print(f"⏱️  超时: {len(results['TIMEOUT'])} 个")
    
    # 详细显示错误
    if results['ERROR']:
        print("\n🔴 详细错误列表:")
        for item in results['ERROR']:
            print(f"\n端点: {item['endpoint']}")
            print(f"说明: {item['description']}")
            print(f"错误: {item['result'].get('message', '未知错误')}")
    
    if results['NOT_FOUND']:
        print("\n❌ 不存在的端点（需要实现）:")
        for item in results['NOT_FOUND']:
            print(f"  - {item['endpoint']:50s} ({item['description']})")

if __name__ == '__main__':
    main()
