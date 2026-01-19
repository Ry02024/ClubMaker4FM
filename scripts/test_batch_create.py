import fm_utils
import batch_create_fields
import json
import sys
import time

def get_field_count():
    try:
        import fm_utils
        import re
        dialog = fm_utils.find_manage_database_dialog()
        if not dialog: return -1
        # 「XXX フィールド」を探す
        for el in dialog.descendants(control_type="Text"):
            t = (el.window_text() or "").strip()
            if "フィールド" in t or "Field" in t:
                m = re.search(r'(\d+)', t)
                if m: return int(m.group(1))
    except: pass
    return -1

def test_single():
    print("--- Test: Single Field Creation with Verification ---", file=sys.stderr)
    
    count_before = get_field_count()
    print(f"  > Count Before: {count_before}", file=sys.stderr)
    
    ts = int(time.time())
    import random
    suffix = random.randint(1000, 9999)
    fname = f"TEST_FIELD_{ts}_{suffix}"
    test_fields = [{"name": fname, "type": "Text"}]
    
    result = batch_create_fields.batch_create_fields(test_fields)
    print(f"  > Batch Create Result: {result}", file=sys.stderr)
    
    time.sleep(1) # Wait for update
    count_after = get_field_count()
    print(f"  > Count After: {count_after}", file=sys.stderr)
    
    if count_after > count_before:
        print("RESULT: SUCCESS (Count increased)")
    else:
        print("RESULT: FAILURE (Count did not increase)")

if __name__ == "__main__":
    test_single()
