import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    try {
        const { fixes } = await request.json();

        if (!fixes || !Array.isArray(fixes) || fixes.length === 0) {
            return NextResponse.json({ success: false, error: 'No fixes provided' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'field_fixer.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // JSON引数を安全にエスケープ
        const fixesJson = JSON.stringify(fixes).replace(/"/g, '\\"');
        const command = `${pythonCommand} "${scriptPath}" "${fixesJson}"`;

        return new Promise((resolve) => {
            exec(command, { timeout: 120000 }, (error, stdout, stderr) => {
                console.log('Field Fixer Output:', stdout);
                if (stderr) console.error('Field Fixer Stderr:', stderr);

                if (error) {
                    resolve(NextResponse.json({
                        success: false,
                        error: error.message,
                        log: stdout
                    }, { status: 500 }));
                } else {
                    try {
                        // 最後の行がJSONのはず
                        const lines = stdout.trim().split('\n');
                        const lastLine = lines[lines.length - 1];
                        const result = JSON.parse(lastLine);
                        resolve(NextResponse.json(result));
                    } catch (e) {
                        resolve(NextResponse.json({
                            success: true,
                            log: stdout
                        }));
                    }
                }
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
