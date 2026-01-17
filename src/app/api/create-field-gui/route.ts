import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    try {
        const { name, type, comment } = await request.json();

        if (!name) {
            return NextResponse.json({ success: false, error: 'Name is required' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'create_field_gui.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // 引数をクォートしてコマンド構築
        const command = `${pythonCommand} "${scriptPath}" "${name}" "${type || 'テキスト'}" "${comment || 'AI生成'}"`;

        return new Promise((resolve) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error('GUI Create Error:', error);
                    resolve(NextResponse.json({ success: false, error: error.message, details: stdout }, { status: 500 }));
                    return;
                }
                resolve(NextResponse.json({ success: true, output: stdout }));
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
