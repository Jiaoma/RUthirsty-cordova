#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from openai import OpenAI

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# 全局变量
config = {}
case_data = {}
game_state = {
    "current_round": 0,
    "dialogue_history": [],
    "max_rounds": 10
}

def load_config():
    """加载配置文件"""
    global config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def load_case():
    """加载案例数据"""
    global case_data
    case_file = config.get('case_file', 'cases/example_case.json')
    with open(case_file, 'r', encoding='utf-8') as f:
        case_data = json.load(f)
    return case_data

def init_openai_client():
    """初始化OpenAI客户端"""
    return OpenAI(
        api_key=config['openai_api_key'],
        base_url=config['openai_api_base']
    )

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
    client = init_openai_client()

    # 构建对话历史
    history_text = "\n".join([
        f"{msg['speaker']}: {msg['content']}"
        for msg in dialogue_history
    ])

    user_prompt = f"""当前对话历史：
{history_text}

请为玩家（{case_data['player_role']}）生成4个可选的回复选项。这些选项应该：
1. 反映不同的沟通策略（如：合作、防御、质疑、建设性等）
2. 有不同的情绪强度
3. 符合角色的性格特点
4. 可以直接复制到聊天软件中使用

当前是第{game_state['current_round']}轮，最多{game_state['max_rounds']}轮。
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
    """初始化游戏"""
    global game_state

    load_config()
    load_case()

    game_state = {
        "current_round": 0,
        "dialogue_history": case_data['initial_dialogue'].copy(),
        "max_rounds": config['max_rounds']
    }

    return jsonify({
        "success": True,
        "case": {
            "title": case_data['title'],
            "background": case_data['background'],
            "characters": case_data['characters'],
            "player_role": case_data['player_role'],
            "context": case_data.get('context', '')
        },
        "initial_dialogue": case_data['initial_dialogue'],
        "max_rounds": config['max_rounds']
    })

@app.route('/api/get_options', methods=['POST'])
def get_options():
    """获取对话选项"""
    try:
        result = generate_options(game_state['dialogue_history'])
        return jsonify({
            "success": True,
            "options": result.get('options', []),
            "round": game_state['current_round'],
            "max_rounds": game_state['max_rounds']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/make_choice', methods=['POST'])
def make_choice():
    """玩家做出选择"""
    data = request.json
    choice = data.get('choice')

    if not choice:
        return jsonify({"success": False, "error": "未提供选择"}), 400

    # 添加玩家的选择到对话历史
    game_state['dialogue_history'].append({
        "speaker": case_data['player_role'],
        "content": choice
    })

    game_state['current_round'] += 1

    try:
        # 生成NPC回应
        result = generate_npc_response(choice, game_state['dialogue_history'])

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
        return jsonify({
            "success": False,
            "error": str(e)
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
