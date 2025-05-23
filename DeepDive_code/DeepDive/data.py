# data.py
import os
import json

def load_user_data(player_id, skills):
    os.makedirs("userdata", exist_ok=True)

    filepath = os.path.join("userdata", f"{player_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            purchased_skills = data.get("purchased_skills", [])
            for skill in skills:
                skill.purchased = skill.name in purchased_skills
            return data.get("coins", 0)
    else:
        return 0

def save_user_data(player_id, total_coins, skills):
    # 自动创建目录
    os.makedirs("userdata", exist_ok=True)

    filepath = os.path.join("userdata", f"{player_id}.json")
    purchased_skills = [skill.name for skill in skills if skill.purchased]
    data = {
        "coins": total_coins,
        "purchased_skills": purchased_skills
    }
    with open(filepath, "w") as f:
        json.dump(data, f)
