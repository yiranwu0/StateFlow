


def get_summary(log_data, model, cache_seed, temperature):
    total_reward = 0
    total_success = 0
    total_turns = 0
    total_cost = 0
    total_p_tokens = 0
    total_c_tokens = 0
    total_time = 0
    total_error_rate = 0

    for l in log_data.values():
        total_reward += l["summary"]['max_reward']
        total_success += 1 if l["summary"]['max_reward'] == 1 else 0
        total_turns += l["summary"]['turns_taken']
        total_cost += l["summary"]['cost']
        total_p_tokens += l["summary"]['prompt_tokens']
        total_c_tokens += l["summary"]['completion_tokens']
        total_time += l["summary"]['time']
        total_error_rate += l['turn_history']['valid_action'].count(False)*1./len(l['turn_history']['valid_action'])
    
    count = len(log_data)
    values = list(log_data.values())
    return {
        "count": count,

        "reward": round(total_reward*1./count, 4),
        "success_rate": round(total_success*1./count, 5),
        "turns": round(total_turns*1./count, 2),
        "cost": round(total_cost*1./count, 8),
        "prompt_tokens": round(total_p_tokens*1./count, 2),
        "completion_tokens": round(total_c_tokens*1./count, 2),
        "total_tokens": round((total_p_tokens+total_c_tokens)*1./count, 2),
        "time": round(total_time*1./count, 2),
        "error_rate": total_error_rate*1./count,

        "model": model,
        "cache_seed": cache_seed,
        "temperature": temperature,
        "max_turn": values[0]["summary"]['turns_max'],
        "start_id": values[0]["task_id"],
        "end_id": values[-1]["task_id"],
    }
