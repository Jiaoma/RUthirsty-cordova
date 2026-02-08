#!/usr/bin/env python3
"""
聊天记录转案例JSON转换脚本
用法: python3 convert_chat.py <聊天记录文件.txt> [输出文件名.json]
"""
import re
import json
import sys
import os
from datetime import datetime

def parse_chat_log(file_path):
    """
    解析聊天记录文件
    格式:
    李嘉诚（100800190） 2025-11-03 09:30:35
    消息内容...
    
    支持的格式变体:
    - 李嘉诚（100800190） 2025-11-03 09:30:35
    - 李嘉诚（100800190） 2025-11-03 10:04:4
    - 李嘉诚（100800190） 2025-11 03 10:04:4
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按行分割
    lines = content.strip().split('\n')
    
    messages = []
    current_speaker = None
    current_content = []
    current_time = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测是否是消息头 (发送者 + 时间)
        # 格式: 李嘉诚（100800190） 2025-11-03 09:30:35
        # 支持中文括号（ ）和英文括号 ( )
        # 支持时间格式: 2025-11-03 10:04:04 或 2025-11-03 10:04:4
        # 也支持: 2025-11 03 10:04:4
        
        # 匹配发送者 (支持中文/英文括号)
        header_match = re.match(
            r'^([^\s（(]+)[（(](\d+)[）)]\s+(\d{4}[-年]?\d{1,2}[-月]?\d{1,2})[\sT](\d{1,2}:\d{1,2}(?::\d{1,2})?)',
            line
        )
        
        if header_match:
            # 保存上一条消息
            if current_speaker and current_content:
                messages.append({
                    'speaker': current_speaker,
                    'content': '\n'.join(current_content).strip(),
                    'time': current_time
                })
            
            # 开始新消息
            current_speaker = header_match.group(1)
            
            # 标准化时间格式
            time_part = header_match.group(4)
            time_parts = time_part.split(':')
            if len(time_parts) == 2:
                # 补全秒数
                time_part += ':00'
            
            current_time = header_match.group(3).replace('-', '-').replace('年', '-').replace('月', '-') + ' ' + time_part
            current_content = []
        else:
            # 消息内容
            if current_speaker:
                # 过滤特殊消息类型（如【卡片消息】、［图片）等）
                if not re.match(r'^[\s【\[\]（）()（）]+$', line):
                    current_content.append(line)
    
    # 保存最后一条消息
    if current_speaker and current_content:
        messages.append({
            'speaker': current_speaker,
            'content': '\n'.join(current_content).strip(),
            'time': current_time
        })
    
    return messages

def extract_characters(messages):
    """
    从消息中提取角色信息
    """
    characters = {}
    
    for msg in messages:
        name = msg['speaker']
        if name not in characters:
            # 根据消息内容推断角色特点
            personality = infer_personality(msg['content'])
            characters[name] = {
                'name': name,
                'role': '团队成员',
                'personality': personality,
                'team': '待定'
            }
    
    return list(characters.values())

def infer_personality(content):
    """
    根据消息内容推断性格特点
    """
    content_lower = content.lower()
    
    if '同意' in content or '好的' in content or '行' in content:
        return "配合度高，积极响应"
    elif '?' in content or '？' in content:
        return "善于提问，关注细节"
    elif len(content) > 100:
        return "表达详细，考虑周全"
    elif '收到' in content or '明白' in content:
        return "响应迅速，态度积极"
    else:
        return "沟通直接，简洁明了"

def create_case_background(messages):
    """
    根据聊天记录生成案例背景
    """
    if not messages:
        return "无"
    
    first_msg = messages[0]
    last_msg = messages[-1]
    num_messages = len(messages)
    num_people = len(set(m['speaker'] for m in messages))
    
    background = f"""这是一个关于团队协作沟通的案例。
背景：{first_msg['time']} 开始的话题讨论。
涉及人员：{num_people} 人，对话 {num_messages} 条。
截止时间：{last_msg['time']}。

这是一个真实的团队工作沟通场景。"""

    return background

def create_case_context(messages, player_name):
    """
    生成玩家扮演的情境描述
    """
    # 查找玩家发送的消息
    player_msgs = [m for m in messages if m['speaker'] == player_name]
    
    context = f"""你扮演的是 {player_name}。

在这次团队讨论中，你共发送了 {len(player_msgs)} 条消息。

请从你的角度出发，体验这次沟通。思考：
1. 你的沟通方式是否有效？
2. 其他团队成员的反应如何？
3. 如果换一种方式沟通，结果会有什么不同？

请做出你的选择，体验不同的沟通策略。"""

    return context

def convert_chat_to_case(chat_file_path, output_file=None, player_role=None, title=None):
    """
    转换聊天记录为案例JSON
    """
    # 解析聊天记录
    print(f"📖 读取聊天记录: {chat_file_path}")
    messages = parse_chat_log(chat_file_path)
    print(f"   解析到 {len(messages)} 条消息")
    
    # 提取角色
    characters = extract_characters(messages)
    print(f"   发现 {len(characters)} 个角色")
    
    # 确定玩家角色
    if not player_role:
        # 默认选择发送消息最多的人
        msg_counts = {}
        for msg in messages:
            msg_counts[msg['speaker']] = msg_counts.get(msg['speaker'], 0) + 1
        player_role = max(msg_counts, key=msg_counts.get)
        print(f"   自动选择玩家角色: {player_role}")
    
    # 生成背景
    background = create_case_background(messages)
    
    # 生成情境
    context = create_case_context(messages, player_role)
    
    # 准备初始对话（取前10条）
    initial_dialogue = []
    for msg in messages[:10]:
        content = msg['content']
        # 过滤特殊消息类型
        if content and not content.startswith('['):
            initial_dialogue.append({
                'speaker': msg['speaker'],
                'content': content[:500]  # 限制长度
            })
        if len(initial_dialogue) >= 8:
            break
    
    # 构建案例JSON
    case_data = {
        'title': title or f"团队沟通案例 - {datetime.now().strftime('%Y-%m-%d')}",
        'background': background,
        'characters': characters,
        'initial_dialogue': initial_dialogue,
        'player_role': player_role,
        'context': context
    }
    
    # 保存
    if not output_file:
        output_file = os.path.splitext(chat_file_path)[0] + '.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(case_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 案例已保存到: {output_file}")
    print(f"\n案例概要:")
    print(f"   标题: {case_data['title']}")
    print(f"   角色数: {len(characters)}")
    print(f"   初始对话: {len(initial_dialogue)} 条")
    print(f"   玩家角色: {player_role}")
    
    return case_data

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n使用示例:")
        print(f"  {sys.argv[0]} chat_log.txt")
        print(f"  {sys.argv[0]} chat_log.txt -o my_case.json -p 张伟")
        print(f"  {sys.argv[0]} chat_log.txt -t '自定义标题'")
        sys.exit(1)
    
    chat_file = sys.argv[1]
    
    if not os.path.exists(chat_file):
        print(f"❌ 文件不存在: {chat_file}")
        sys.exit(1)
    
    # 解析参数
    output_file = None
    player_role = None
    title = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '-o' or sys.argv[i] == '--output':
            output_file = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '-p' or sys.argv[i] == '--player':
            player_role = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == '-t' or sys.argv[i] == '--title':
            title = sys.argv[i+1]
            i += 2
        else:
            i += 1
    
    convert_chat_to_case(chat_file, output_file, player_role, title)

if __name__ == '__main__':
    main()
