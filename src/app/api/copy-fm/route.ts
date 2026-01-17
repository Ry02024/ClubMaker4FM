import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';

export async function POST(request: Request) {
    let tmpXmlFile: string | null = null;
    try {
        const { xml } = await request.json();

        if (!xml) {
            return NextResponse.json({ success: false, error: 'No XML provided' }, { status: 400 });
        }

        // コマンドライン引数の長さ制限や特殊文字のエスケープ問題を避けるため、一時ファイルに保存
        const tmpDir = os.tmpdir();
        tmpXmlFile = path.join(tmpDir, `fm_clip_${Date.now()}.xml`);
        fs.writeFileSync(tmpXmlFile, xml, { encoding: 'utf8' });

        // Pythonスクリプトのパス
        const scriptPath = path.join(process.cwd(), 'scripts', 'set_fm_clipboard.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        const command = `${pythonCommand} "${scriptPath}" "${tmpXmlFile}"`;

        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                // クリーンアップ
                if (tmpXmlFile && fs.existsSync(tmpXmlFile)) {
                    try { fs.unlinkSync(tmpXmlFile); } catch (e) { }
                }

                if (error) {
                    console.error('Clipboard Error:', stderr || stdout);
                    resolve(NextResponse.json({
                        success: false,
                        error: stderr || stdout || error.message
                    }, { status: 500 }));
                    return;
                }
                resolve(NextResponse.json({ success: true, result: stdout.trim() }));
            });
        });
    } catch (err: any) {
        if (tmpXmlFile && fs.existsSync(tmpXmlFile)) {
            try { fs.unlinkSync(tmpXmlFile); } catch (e) { }
        }
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
