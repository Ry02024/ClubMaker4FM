import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
    try {
        const { currentFields, context } = await request.json();

        if (!currentFields || !Array.isArray(currentFields)) {
            return NextResponse.json({ success: false, error: 'No current fields provided' }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'scripts', 'suggest_field_fix.py');
        const venvPythonPath = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
        const pythonCommand = fs.existsSync(venvPythonPath) ? `"${venvPythonPath}"` : 'python';

        // 現在のフィールドとコンテキストをJSONで渡す
        const inputData = JSON.stringify({ currentFields, context: context || '' }).replace(/"/g, '\\"');
        const command = `${pythonCommand} "${scriptPath}" "${inputData}"`;

        return new Promise((resolve) => {
            exec(command, { timeout: 60000 }, (error, stdout, stderr) => {
                console.log('Suggest Field Fix Output:', stdout);
                if (stderr) console.error('Suggest Field Fix Stderr:', stderr);

                if (error) {
                    resolve(NextResponse.json({
                        success: false,
                        error: error.message
                    }, { status: 500 }));
                } else {
                    try {
                        const lines = stdout.trim().split('\n');
                        const lastLine = lines[lines.length - 1];
                        const result = JSON.parse(lastLine);
                        resolve(NextResponse.json(result));
                    } catch (e) {
                        resolve(NextResponse.json({
                            success: false,
                            error: 'Failed to parse AI response',
                            raw: stdout
                        }, { status: 500 }));
                    }
                }
            });
        });
    } catch (err: any) {
        return NextResponse.json({ success: false, error: err.message }, { status: 500 });
    }
}
