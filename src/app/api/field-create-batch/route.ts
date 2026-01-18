import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    try {
        const { fields } = await request.json();

        if (!fields || !Array.isArray(fields)) {
            return NextResponse.json({ success: false, error: 'Fields array is required' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'batch_create_fields.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // フィールドリストをテンポラリファイルに書き出す (コマンドライン引数の長さ制限回避)
        const tempFilePath = path.join(process.cwd(), 'data', 'temp_create_batch.json');
        fs.writeFileSync(tempFilePath, JSON.stringify(fields, null, 2), 'utf-8');

        const command = `${pythonCommand} "${scriptPath}" "${tempFilePath}"`;

        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                // テンポラリファイルを削除
                try { fs.unlinkSync(tempFilePath); } catch (e) { }

                if (error) {
                    console.error('Batch Create Error:', error);
                    resolve(NextResponse.json({
                        success: false,
                        error: error.message,
                        details: stdout,
                        stderr: stderr
                    }, { status: 500 }));
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    resolve(NextResponse.json(result));
                } catch (e) {
                    resolve(NextResponse.json({ success: true, output: stdout }));
                }
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
