#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队矛盾冲突模拟器 - 后端服务
增加详细日志便于调试
"""

import os
import sys
import glob

# 启动时清理代理环境变量
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'REQUESTS_TIMEOUT', 'CURL_CA_BUNDLE']:
    if var in os.environ:
        del os.environ[var]

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from openai import OpenAI

# 初始化Flask
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# 全局变量
config = {}
case_data = {}
game_state = {}

# 调试开关
DEBUG = True

def log(msg):
    """打印调试日志"""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)

def load_config():
    """加载配置文件"""
    global config
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.json')
        log(f"加载配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        log(f"配置加载成功: API={config.get('openai_api_base', 'N/A')[:50]}...")
        return config
    except Exception as e:
        log(f"加载配置失败: {e}")
        raise

def load_case():
    """加载案例数据"""
    global case_data
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        case_file_relative = config.get('case_file', 'cases/example_case.json')
        case_file = os.path.join(project_root, case_file_relative)
        log(f"加载案例文件: {case_file}")
        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        log(f"案例加载成功: {case_data.get('title', 'N/A')}")
        return case_data
    except Exception as e:
        log(f"加载案例失败: {e}")
        raise

def init_openai_client():
    """初始化OpenAI客户端"""
    try:
        api_key = config.get('openai_api_key', '')
        api_base = config.get('openai_api_base', '')
        log(f"初始化OpenAI客户端: base={api_base[:50]}...")
        
        client = OpenAI(api_key=api_key, base_url=api_base)
        log("OpenAI客户端初始化成功")
        return client
    except Exception as e:
        log(f"初始化OpenAI客户端失败: {e}")
        raise

def generate_system_prompt():
    """生成系统提示词"""
    characters_desc = "\n".join([
        f"- {char['name']}（{char['role']}）：{char['personality']}，所属{char['team']}"
        for char in case_data['characters']
    ])

    return f"""你是一个团队冲突模拟器的AI助手。你需要根据以下背景信息来模拟团队成员之间的对话。

案例背景：
{case_data['background']}

角色信息：
{characters_desc}

当前情境：
{case_data.get('context', '')}

玩家扮演的角色是：{case_data['player_role']}

游戏规则：
1. 游戏最多进行{game_state['max_rounds']}轮对话
2. 每轮你需要根据对话历史，为玩家提供4个可选的回复选项（A、B、C、D）
3. 这些选项应该反映不同的沟通策略和情绪强度
4. 选项可以包含@符号来通知其他成员
5. 根据玩家的选择，模拟其他角色的真实反应
6. 要考虑每个角色的性格特点和团队背景
7. 对话可以包含真实的情绪（包括激烈的争吵），但要保持专业性
8. 当接近最大轮数时，要引导对话走向结束

请始终以JSON格式回复，包含以下字段：
- options: 4个选项的数组，每个选项包含label（A/B/C/D）和content（对话内容）
- npc_response: 如果玩家已经做出选择，这里是其他角色的回应
- round_summary: 本轮的简短总结
- is_end: 是否应该结束游戏
- end_summary: 如果游戏结束，提供整体总结和反思
"""

def generate_options(dialogue_history):
    """生成对话选项"""
    log(f"generate_options: 对话历史={len(dialogue_history)}条")
    
    try:
        client = init_openai_client()
    except Exception as e:
        log(f"初始化OpenAI客户端失败: {e}")
        raise Exception(f"初始化AI客户端失败: {e}")

    # 构建对话历史
    history_text = "\n".join([
        f"{msg['speaker']}: {msg['content']}"
        for msg in dialogue_history
    ])
    log(f"构建对话历史完成，共{len(history_text)}字符")

    user_prompt = f"""当前对话历史：
{history_text}

请为玩家（{case_data.get('player_role', '未知')}）生成4个可选的回复选项。这些选项应该：
1. 反映不同的沟通策略（如：合作、防御、质疑、建设性等）
2. 有不同的情绪强度
3. 符合角色的性格特点
4. 可以直接复制到聊天软件中使用

当前是第{game_state.get('current_round', 0)}轮，最多{game_state.get('max_rounds', 10)}轮。
"""

    try:
        log(f"调用AI API，模型={config.get('model', 'N/A')}")
        response = client.chat.completions.create(
            model=config.get('model', 'gpt-4'),
            messages=[
                {"role": "system", "content": generate_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.get('temperature', 0.8),
            response_format={"type": "json_object"}
        )
        log("AI API调用成功")
        
        result = json.loads(response.choices[0].message.content)
        log(f"解析结果: {len(result.get('options', []))}个选项")
        return result
    except Exception as e:
        log(f"AI API调用失败: {type(e).__name__}: {e}")
        raise Exception(f"AI生成失败: {type(e).__name__}: {str(e)[:200]}")

def generate_npc_response(player_choice, dialogue_history):
    """生成NPC回应"""
    client = init_openai_client()

    history_text = "\n".join([
        f"{msg['speaker']}: {msg['content']}"
        for msg in dialogue_history
    ])

    user_prompt = f"""对话历史：
{history_text}

玩家（{case_data['player_role']}）选择了：
{player_choice}

请模拟其他角色对此的反应。要考虑：
1. 每个角色的性格特点
2. 当前的对话氛围
3. 团队的实际情况
4. 真实的人际互动

当前是第{game_state['current_round']}轮，最多{game_state['max_rounds']}轮。
如果接近最大轮数，要考虑如何自然地结束对话。

请返回JSON格式，包含：
- npc_responses: NPC回应的数组，每个包含speaker和content
- round_summary: 本轮总结
- is_end: 是否结束游戏
- end_summary: 如果结束，提供总结和反思
"""

    response = client.chat.completions.create(
        model=config['model'],
        messages=[
            {"role": "system", "content": generate_system_prompt()},
            {"role": "user", "content": user_prompt}
        ],
        temperature=config['temperature'],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/init', methods=['GET'])
def init_game():
    """初始化游戏，可选指定玩家角色"""
    global game_state, case_data

    load_config()
    load_case()

    # 获取可选的玩家角色列表
    characters = case_data['characters']

    return jsonify({
        "success": True,
        "case": {
            "title": case_data['title'],
            "background": case_data['background'],
            "characters": characters,
            "default_player_role": case_data['player_role'],
            "context": case_data.get('context', '')
        },
        "initial_dialogue": case_data['initial_dialogue'],
        "max_rounds": config['max_rounds']
    })

import glob

@app.route('/api/cases', methods=['GET'])
def list_cases():
    """获取案例列表"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cases_dir = os.path.join(project_root, 'cases')
        
        cases = []
        for filepath in glob.glob(os.path.join(cases_dir, '*.json')):
            with open(filepath, 'r', encoding='utf-8') as f:
                case = json.load(f)
                filename = os.path.basename(filepath)
                cases.append({
                    'id': filename.replace('.json', ''),
                    'title': case.get('title', filename),
                    'description': case.get('background', '')[:100] + '...' if len(case.get('background', '')) > 100 else case.get('background', ''),
                    'characters_count': len(case.get('characters', [])),
                    'filename': filename
                })
        
        return jsonify({
            "success": True,
            "cases": cases
        })
    except Exception as e:
        log(f"获取案例列表失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/select_case', methods=['POST'])
def select_case():
    """选择案例并加载"""
    global case_data, config
    
    data = request.json
    case_filename = data.get('case_filename')
    
    if not case_filename:
        return jsonify({"success": False, "error": "未指定案例"}), 400
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        case_file = os.path.join(project_root, 'cases', case_filename)
        
        with open(case_file, 'r', encoding='utf-8') as f:
            case_data = json.load(f)
        
        load_config()
        
        return jsonify({
            "success": True,
            "case": {
                "title": case_data['title'],
                "background": case_data['background'],
                "characters": case_data['characters'],
                "default_player_role": case_data['player_role'],
                "context": case_data.get('context', '')
            },
            "initial_dialogue": case_data['initial_dialogue'],
            "max_rounds": config['max_rounds']
        })
    except Exception as e:
        log(f"加载案例失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/start', methods=['POST'])
def start_game():
    """开始游戏，指定玩家角色"""
    global game_state, case_data

    data = request.json
    player_role = data.get('player_role')

    # 验证角色是否有效
    valid_roles = [char['name'] for char in case_data['characters']]
    if player_role not in valid_roles:
        return jsonify({"success": False, "error": "无效的角色"}), 400

    load_config()

    game_state = {
        "current_round": 0,
        "dialogue_history": case_data['initial_dialogue'].copy(),
        "max_rounds": config['max_rounds'],
        "player_role": player_role
    }

    return jsonify({
        "success": True,
        "player_role": player_role,
        "current_round": 0,
        "max_rounds": config['max_rounds']
    })

@app.route('/api/get_options', methods=['POST'])
def get_options():
    """获取对话选项"""
    log("=== get_options 被调用 ===")
    try:
        # 检查游戏状态
        if not game_state:
            log("错误: 游戏未初始化，请先调用 /api/init 或 /api/start")
            return jsonify({
                "success": False,
                "error": "游戏未初始化，请刷新页面重试"
            }), 400
        
        log(f"当前轮次: {game_state.get('current_round', 0)}/{game_state.get('max_rounds', 10)}")
        log(f"对话历史: {len(game_state.get('dialogue_history', []))}条")
        
        result = generate_options(game_state.get('dialogue_history', []))
        
        log(f"成功生成 {len(result.get('options', []))} 个选项")
        return jsonify({
            "success": True,
            "options": result.get('options', []),
            "round": game_state.get('current_round', 0),
            "max_rounds": game_state.get('max_rounds', 10)
        })
    except Exception as e:
        log(f"get_options 错误: {type(e).__name__}: {e}")
        return jsonify({
            "success": False,
            "error": f"生成选项失败: {str(e)[:300]}"
        }), 500

@app.route('/api/make_choice', methods=['POST'])
def make_choice():
    """玩家做出选择"""
    log("=== make_choice 被调用 ===")
    data = request.json
    choice = data.get('choice')

    if not choice:
        log("错误: 未提供选择")
        return jsonify({"success": False, "error": "未提供选择"}), 400

    # 添加玩家的选择到对话历史
    player = game_state.get('player_role', case_data.get('player_role', '未知'))
    log(f"玩家选择: {player[:20]}...")
    
    game_state['dialogue_history'].append({
        "speaker": player,
        "content": choice
    })

    game_state['current_round'] += 1
    log(f"当前轮次: {game_state['current_round']}/{game_state['max_rounds']}")

    try:
        # 生成NPC回应
        log("调用AI生成NPC回应...")
        result = generate_npc_response(choice, game_state['dialogue_history'])
        log(f"NPC回应生成成功: {len(result.get('npc_responses', []))}条")

        # 添加NPC回应到对话历史
        if 'npc_responses' in result:
            for npc_msg in result['npc_responses']:
                game_state['dialogue_history'].append(npc_msg)

        return jsonify({
            "success": True,
            "npc_responses": result.get('npc_responses', []),
            "round_summary": result.get('round_summary', ''),
            "is_end": result.get('is_end', False),
            "end_summary": result.get('end_summary', ''),
            "current_round": game_state['current_round'],
            "max_rounds": game_state['max_rounds']
        })
    except Exception as e:
        log(f"make_choice 错误: {type(e).__name__}: {e}")
        return jsonify({
            "success": False,
            "error": f"处理选择失败: {str(e)[:300]}"
        }), 500

@app.route('/api/get_history', methods=['GET'])
def get_history():
    """获取对话历史"""
    return jsonify({
        "success": True,
        "history": game_state['dialogue_history'],
        "current_round": game_state['current_round'],
        "max_rounds": game_state['max_rounds']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
