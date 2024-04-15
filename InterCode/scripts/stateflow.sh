SEED=41 # for AutoGen caching

python -m experiments.eval_stateflow_sql \
    --data_path ./data/sql/spider/ic_spider_dev.json \
    --env sql \
    --image_name docker-env-sql \
    --log_dir logs/test \
    --max_turns 10 \
    --model gpt-35-turbo-1106 \
    --cache_seed $SEED \
    --verbose \
    
# python -m experiments.eval_stateflow_bash \
#     --data_path ./data/nl2bash/nl2bash_fs_1.json \
#     --env bash \
#     --image_name intercode-nl2bash-fs-1 \
#     --log_dir logs/test/sf_$SEED \
#     --max_turns 10 \
#     --model gpt-35-turbo-1106 \
#     --cache_seed $SEED \
#     --verbose


# python -m experiments.eval_stateflow_bash \
#     --data_path ./data/nl2bash/nl2bash_fs_2.json \
#     --env bash \
#     --image_name intercode-nl2bash-fs-2 \
#     --log_dir logs/test/sf_$SEED \
#     --max_turns 10 \
#     --model gpt-35-turbo-1106 \
#     --cache_seed $SEED \
#     --verbose


# python -m experiments.eval_stateflow_bash \
#     --data_path ./data/nl2bash/nl2bash_fs_3.json \
#     --env bash \
#     --image_name intercode-nl2bash-fs-3 \
#     --log_dir logs/test/sf_$SEED \
#     --max_turns 10 \
#     --model gpt-35-turbo-1106 \
#     --cache_seed $SEED \
#     --verbose


# python -m experiments.eval_stateflow_bash \
#     --data_path ./data/nl2bash/nl2bash_fs_4.json \
#     --env bash \
#     --image_name intercode-nl2bash-fs-4 \
#     --log_dir logs/test/sf_$SEED \
#     --max_turns 10 \
#     --model gpt-35-turbo-1106 \
#     --cache_seed $SEED \
#     --verbose



