import os
import importlib.util

here = os.path.dirname(os.path.abspath(__file__))
main_path = os.path.join(here, "instagram-user-details", "main.py")

spec = importlib.util.spec_from_file_location("main", main_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load module from {main_path}")

main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)
main = main_module.main

if __name__ == "__main__":
    main()