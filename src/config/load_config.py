import yaml 
def load_config(config_path='./src/config/config.yml'):
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Không tìm thấy file config tại đường dẫn: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Lỗi khi parse file YAML: {e}")
        return None


config = load_config()  # dictionary