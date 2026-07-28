from pathlib import Path
def test_required_files():
    root=Path(__file__).parents[1]
    for item in ["site/index.html","site/assets/app.js","backend/app/main.py","database/schema.sql"]:
        assert (root/item).exists()
