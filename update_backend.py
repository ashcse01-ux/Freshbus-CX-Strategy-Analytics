with open('backend/routers/helpdesk.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
code = code.replace('from fastapi import APIRouter, HTTPException', 'from fastapi import APIRouter, HTTPException\nfrom fastapi.responses import FileResponse')

endpoints = """
@router.get("/raw_hd")
async def get_raw_hd():
    file_path = os.path.join(os.path.dirname(__file__), "..", "raw_hd.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Raw HD data not found")

@router.get("/raw_hda")
async def get_raw_hda():
    file_path = os.path.join(os.path.dirname(__file__), "..", "raw_hda.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Raw HDA data not found")
"""
if "get_raw_hd" not in code:
    code += endpoints

with open('backend/routers/helpdesk.py', 'w', encoding='utf-8') as f:
    f.write(code)
