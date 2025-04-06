import requests
import re
import json
import uuid
import time

def get_quiz_structure(max_retries=3):
    """获取题目结构（含自动重试机制）"""
    # 配置请求参数
    api_url = "https://sjtu.aihaoke.net/api/learn/task/exercise/listQuiz"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6ImM0MmU3MGJiLTI2OGYtNGYzMi1hOGFiLTM2YjRlMTFkMjk3NiJ9.Cx85OwnIScvj16LSJVFiCWE3JT885QTwN4k7v_J706gaaVFj25S8ibkVld74BcsEN-td5U2J-qk1fnBIOk56fQ",
        "Content-Type": "application/json",
        "Referer": "https://sjtu.aihaoke.net/student/course/1432/studyTask/22530/evaluation",
        "Origin": "https://sjtu.aihaoke.net"
    }
    
    cookies = {
        "HWWAFSESID": "7f8457375f3335105b",
        "HWWAFSESTIME": "1743904149026",
        "haoke-token": "eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6ImM0MmU3MGJiLTI2OGYtNGYzMi1hOGFiLTM2YjRlMTFkMjk3NiJ9.Cx85OwnIScvj16LSJVFiCWE3JT885QTwN4k7v_J706gaaVFj25S8ibkVld74BcsEN-td5U2J-qk1fnBIOk56fQ"
    }
    
    payload = {
        "requestId": str(uuid.uuid4()),
        "classId": 1432,
        "taskId": 22530
    }

    for attempt in range(max_retries):
        try:
            # 发送请求
            response = requests.post(
                url=api_url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=10
            )
            
            print(f"第{attempt+1}次请求，状态码：{response.status_code}")
            
            # 检查响应状态
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 200:
                raise ValueError(f"API返回异常：{data.get('message')}")
                
            # 解析数据
            quiz_data = parse_quiz_data(data["data"]["quizList"])
            print("成功获取题目结构")
            return quiz_data
            
        except Exception as e:
            print(f"请求失败（第{attempt+1}次）：{str(e)}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 5)  # 指数退避，最大等待5秒
                print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                if 'response' in locals():
                    print("最后错误响应：", response.text[:500])
                return None

def parse_quiz_data(quiz_list):
    """精确解析题目结构"""
    structure = {}
    
    for quiz in quiz_list:
        # 跳过非题目内容
        if "作业反馈" in quiz.get("content", "") or "自评" in quiz.get("content", ""):
            continue
            
        content = quiz["content"]
        item = {
            "quiz_id": quiz["quizId"],
            "main_question": None,
            "sub_questions": [],
            "score": quiz.get("score", 0) / 100,
            "content_preview": content.split("\n")[0]
        }
        
        # 精确匹配主问题号和小题号
        if match := re.search(r"(\d+-\d+)\s*[（(](\d+(?:,\d+)*)[)）]", content):
            item["main_question"] = match.group(1)
            item["sub_questions"] = [int(n) for n in match.group(2).split(",")]
        # 匹配只有主问题号的情况
        elif match := re.search(r"^(\d+-\d+)(?=\s|$)", content):
            item["main_question"] = match.group(1)
        
        # 验证提取结果
        if not item["main_question"]:
            print(f"警告：未能解析题号，quizId={quiz['quizId']}")
            print(f"内容开头：{content[:100]}...")
            continue
            
        structure[quiz["quizId"]] = item
    
    return structure


def generate_display_format(item):
    """生成题号显示格式"""
    display = []
    
    # 处理主问题
    for main in item["main_questions"]:
        parts = main.split('-')
        if len(parts) == 2:
            start, end = map(int, parts)
            if end - start > 10:
                display.append(f"第{start}章")
            else:
                display.append(f"{main}题")
    
    # 处理子问题
    if item["sub_questions"]:
        # 合并连续数字
        ranges = []
        start = end = item["sub_questions"][0]
        
        for num in item["sub_questions"][1:]:
            if num == end + 1:
                end = num
            else:
                ranges.append(f"{start}" if start == end else f"{start}-{end}")
                start = end = num
        ranges.append(f"{start}" if start == end else f"{start}-{end}")
        
        display.append(f"（{','.join(ranges)}）")
    
    return "".join(display)

def save_to_json(data, filename="quiz_structure.json"):
    """保存数据到JSON文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"数据已保存到 {filename}")

if __name__ == "__main__":
    # 获取题目结构
    quiz_data = get_quiz_structure(max_retries=3)
    
    #if quiz_data:
        # 打印所有结果（完整输出）
        #print("\n完整的题目结构解析：")
        #print(f"\n题目ID: {qid}")
            #print("-"*50)
            ##print("-"*50)
        
        # 保存完整数据
        #save_to_json(quiz_data)
        #print("\n所有题目解析已完成！")