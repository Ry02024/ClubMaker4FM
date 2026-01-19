'use client';

import { useState, useEffect } from 'react';
import { generateFieldsXML, generateTableXML, generateLayoutXML, FMTable } from '@/lib/fm-xml';

const PRESET_PROMPT = `夜店クラブの「伝票・売上管理」ミニマムシステム
- 伝票テーブル(dp): 日付, tableno, total, castid, custid, paytype
- 設定テーブル(app): var_cast (JSON), 当日売上集計
- 1画面入力→自動計算→ランキング出力`;

export default function Home() {
  const [prompt, setPrompt] = useState(PRESET_PROMPT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [viewMode, setViewMode] = useState<'schema' | 'layout' | 'fixer'>('schema');
  const [design, setDesign] = useState<{
    tables: FMTable[],
    layouts?: any[],
    thoughts?: string[]
  } | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [status, setStatus] = useState<{ msg: string; isError: boolean } | null>(null);
  const [cooldown, setCooldown] = useState(0);

  // Theme State
  const [theme, setTheme] = useState<'dark' | 'dawn' | 'light'>('dark');

  // ThemeをHTMLタグに適用
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // フィールド修整用のstate
  const [currentFields, setCurrentFields] = useState<{ name: string, type: string }[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [selectedFixes, setSelectedFixes] = useState<Set<number>>(new Set());
  const [isLoadingFields, setIsLoadingFields] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isFixing, setIsFixing] = useState(false);

  // クールダウンのカウントダウン
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(prev => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  // スクリーンショット一覧を取得
  const fetchScreenshots = async () => {
    try {
      const res = await fetch('/api/screenshots');
      const data = await res.json();
      setScreenshots(data.screenshots || []);
    } catch (err) {
      console.error('Failed to fetch screenshots');
    }
  };

  useEffect(() => {
    fetchScreenshots();
  }, []);

  const handleLaunchFM = async () => {
    setIsLaunching(true);
    setStatus({ msg: 'FileMakerを起動中...', isError: false });
    try {
      const res = await fetch('/api/launch-fm', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ FileMakerを起動しました', isError: false });
    } catch (err: any) {
      setStatus({ msg: `❌ 起動失敗: ${err.message}`, isError: true });
    } finally {
      setIsLaunching(false);
    }
  };

  const handleCapture = async () => {
    setIsCapturing(true);
    setStatus({ msg: '画面をキャプチャ中...', isError: false });
    try {
      const res = await fetch('/api/capture-screen', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ キャプチャ完了', isError: false });
      await fetchScreenshots();
    } catch (err: any) {
      setStatus({ msg: `❌ キャプチャ失敗: ${err.message}`, isError: true });
    } finally {
      setIsCapturing(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt) {
      setStatus({ msg: '指示を入力してください', isError: true });
      return;
    }
    setIsGenerating(true);
    setStatus({ msg: 'AIがFileMakerの設計図を作成中...', isError: false });

    try {
      const res = await fetch('/api/generate-design', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || '生成に失敗しました');
      }

      let extractedDesign = data.design;
      if (!extractedDesign.tables && extractedDesign.design?.tables) {
        extractedDesign = extractedDesign.design;
      }
      if (!extractedDesign.tables && extractedDesign.table) {
        extractedDesign.tables = Array.isArray(extractedDesign.table) ? extractedDesign.table : [extractedDesign.table];
      }
      if (!extractedDesign.tables && extractedDesign.layouts) {
        extractedDesign.tables = [];
      }

      if (!extractedDesign.tables || !Array.isArray(extractedDesign.tables)) {
        console.error('Invalid design structure:', extractedDesign);
        const details = extractedDesign.details ? `\n詳細:\n${extractedDesign.details.join('\n')}` : '';
        throw new Error(`AIの返答形式が正しくありません (tablesが見つかりません)。内容: ${JSON.stringify(extractedDesign).substring(0, 100)}...${details}`);
      }

      setDesign({
        tables: extractedDesign.tables,
        layouts: extractedDesign.layouts || [],
        thoughts: extractedDesign.thoughts || []
      });
      if (extractedDesign.layouts?.length > 0) {
        setViewMode('layout');
      }
      setStatus({ msg: '✅ 設計図が完成しました！内容を確認してください', isError: false });
    } catch (err: any) {
      console.error(err);
      setStatus({ msg: `❌ エラー: ${err.message}`, isError: true });
    } finally {
      setIsGenerating(false);
      setCooldown(10);
    }
  };

  const copyToFM = async (xml: string) => {
    setStatus({ msg: 'クリップボードに登録中...', isError: false });
    try {
      const res = await fetch('/api/copy-fm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ xml }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: '✅ クリップボードに登録完了！FileMakerで貼り付けできます。', isError: false });
    } catch (err: any) {
      setStatus({ msg: `❌ エラー: ${err.message}`, isError: true });
    }
  };

  const handleCreateFieldGUI = async (name: string, type: string, comment: string = 'AI生成') => {
    setStatus({ msg: `GUI操作でフィールド "${name}" を生成中...`, isError: false });
    try {
      const res = await fetch('/api/create-field-gui', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, type, comment }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setStatus({ msg: `✅ フィールド "${name}" の生成命令を送信しました（FileMakerを確認してください）`, isError: false });
    } catch (err: any) {
      console.error(err);
      setStatus({ msg: `❌ GUI生成エラー: ${err.message}`, isError: true });
    }
  };

  const handleFinalizeFM = async () => {
    setStatus({ msg: '変更を保存してダイアログを閉じています...', isError: false });
    try {
      const res = await fetch('/api/finalize-fm-dialog', { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
    } catch (err: any) {
      console.error('Finalize failed:', err);
    }
  };

  const handleBatchCreateGUI = async (fields: any[]) => {
    if (!confirm(`${fields.length} 個のフィールドを順番にGUI生成します。\n既存フィールドはスキップされます。\n\n開始してよろしいですか？`)) return;

    setStatus({ msg: 'FileMakerの現在の状態を確認中...', isError: false });
    let existingFields: string[] = [];
    try {
      const res = await fetch(`/api/get-fm-fields?t=${Date.now()}`);
      const data = await res.json();
      if (data.success) {
        existingFields = data.fields.map((f: any) => f.name.toLowerCase());
      }
    } catch (err) {
      console.warn('進捗の取得に失敗しました。全件作成を試みます。', err);
    }
    const remainingFields = fields.filter(f => !existingFields.includes(f.name.toLowerCase()));

    if (remainingFields.length === 0) {
      setStatus({ msg: '✅ 全てのフィールドは既に存在します。', isError: false });
      await handleFinalizeFM();
      return;
    }

    // setStatus({ msg: 'FileMakerの現在の状態を確認中...', isError: false });
    // let existingFields: string[] = [];
    // try {
    //   const res = await fetch(`/api/get-fm-fields?t=${Date.now()}`);
    //   const data = await res.json();
    //   if (data.success) {
    //     existingFields = data.fields.map((f: any) => f.name.toLowerCase());
    //   }
    // } catch (err) {
    //   console.warn('進捗の取得に失敗しました。全件作成を試みます。', err);
    // }
    // const remainingFields = fields.filter(f => !existingFields.includes(f.name.toLowerCase()));

    // if (remainingFields.length === 0) {
    //   setStatus({ msg: '✅ 全てのフィールドは既に存在します。', isError: false });
    //   await handleFinalizeFM();
    //   return;
    // }

    setStatus({ msg: `${remainingFields.length} 件のフィールドを一括生成中...（FileMakerを確認してください）`, isError: false });

    try {
      const res = await fetch('/api/field-create-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: remainingFields }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      setStatus({ msg: `✅ ${data.count || remainingFields.length} 件のフィールド生成が完了しました。`, isError: false });
      await handleFinalizeFM();
    } catch (err: any) {
      console.error(err);
      setStatus({ msg: `❌ 一括生成エラー: ${err.message}`, isError: true });
    }
  };

  const handleLoadCurrentFields = async () => {
    setIsLoadingFields(true);
    setStatus({ msg: 'FileMakerから現在のフィールドを読み取っています...', isError: false });
    try {
      const res = await fetch(`/api/get-fm-fields?t=${Date.now()}`);
      const data = await res.json();
      if (data.success) {
        setCurrentFields(data.fields);
        setSuggestions([]);
        setSelectedFixes(new Set());
        setStatus({ msg: `✅ ${data.fields.length} 件のフィールドを読み取りました`, isError: false });
      } else {
        throw new Error(data.error);
      }
    } catch (err: any) {
      setStatus({ msg: `❌ 読み取りエラー: ${err.message}`, isError: true });
    } finally {
      setIsLoadingFields(false);
    }
  };

  const handleSuggestFixes = async () => {
    if (currentFields.length === 0) {
      setStatus({ msg: '先にフィールドを読み取ってください', isError: true });
      return;
    }
    setIsSuggesting(true);
    setStatus({ msg: 'AIが最適化を分析中...', isError: false });
    try {
      const res = await fetch('/api/suggest-field-fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentFields, context: prompt }),
      });
      const data = await res.json();
      if (data.success) {
        setSuggestions(data.suggestions);
        const autoSelect = new Set<number>();
        data.suggestions.forEach((s: any, i: number) => {
          if (s.should_fix) autoSelect.add(i);
        });
        setSelectedFixes(autoSelect);
        setStatus({ msg: `✅ ${data.suggestions.length} 件の提案を取得しました`, isError: false });
      } else {
        throw new Error(data.error);
      }
    } catch (err: any) {
      setStatus({ msg: `❌ AI提案エラー: ${err.message}`, isError: true });
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleBatchFix = async () => {
    if (selectedFixes.size === 0) {
      setStatus({ msg: '修整する項目を選択してください', isError: true });
      return;
    }
    if (!confirm(`⚠️ ${selectedFixes.size} 件のフィールドを修整します。\n\nこの操作は元に戻せません。\nFileMakerのバックアップを取っていますか？`)) {
      return;
    }
    setIsFixing(true);
    setStatus({ msg: `${selectedFixes.size} 件のフィールドを修整中...`, isError: false });
    try {
      const fixList = Array.from(selectedFixes).map(i => ({
        old_name: suggestions[i].old_name,
        new_name: suggestions[i].new_name,
        new_type: suggestions[i].new_type !== suggestions[i].old_type ? suggestions[i].new_type : null,
        comment: suggestions[i].comment || 'ClubMaker最適化'
      }));
      const res = await fetch('/api/field-fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fixes: fixList }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus({ msg: `✅ ${data.succeeded}/${data.total} 件の修整が完了しました`, isError: false });
        // フィールドを再読み込み
        handleLoadCurrentFields();
      } else {
        throw new Error(data.error);
      }
    } catch (err: any) {
      setStatus({ msg: `❌ 修整エラー: ${err.message}`, isError: true });
    } finally {
      setIsFixing(false);
    }
  };

  const toggleFix = (index: number) => {
    const newSet = new Set(selectedFixes);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setSelectedFixes(newSet);
  };

  return (
    <main className="min-h-screen bg-app-bg text-text-main p-6 font-sans selection:bg-purple-500/30 transition-colors duration-300">
      {/* 背景装飾 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-pink-900/10 blur-[120px] rounded-full"></div>
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <header className="flex justify-between items-center bg-panel-bg backdrop-blur-md border border-panel-border p-4 rounded-2xl shadow-xl transition-colors">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-tr from-purple-600 to-pink-600 rounded-xl flex items-center justify-center font-bold text-xl shadow-lg shadow-purple-500/20 text-white">
              C
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-text-main to-text-sub bg-clip-text text-transparent">
                CLUB MAKER
              </h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-text-sub font-bold">
                AI Powered FileMaker Automator
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Theme Toggle Button */}
            {/* Theme Toggle Button */}
            <button
              onClick={() => {
                // Cycle: Night (dark) -> Dawn -> Light -> Night
                if (theme === 'dark') setTheme('dawn');
                else if (theme === 'dawn') setTheme('light');
                else setTheme('dark');
              }}
              className="p-2.5 bg-panel-bg hover:bg-white/10 border border-panel-border rounded-xl transition-all text-xl"
              title={
                theme === 'dark' ? "Switch to Dawn Mode" :
                  theme === 'dawn' ? "Switch to Light Mode" :
                    "Switch to Night Mode"
              }
            >
              {
                theme === 'dark' ? '🌙' :
                  theme === 'dawn' ? '🌅' :
                    '☀️'
              }
            </button>
            <div className="w-px h-8 bg-panel-border mx-1"></div>

            <button
              onClick={handleLaunchFM}
              disabled={isLaunching}
              className="flex items-center gap-2 px-5 py-2.5 bg-panel-bg hover:bg-white/10 border border-panel-border rounded-xl transition-all duration-300 text-sm font-semibold active:scale-95 disabled:opacity-50 text-text-main"
            >
              <span className={isLaunching ? 'animate-spin' : ''}>🚀</span>
              {isLaunching ? '起動中...' : 'FileMaker 起動'}
            </button>
            <button
              onClick={handleCapture}
              disabled={isCapturing}
              className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-purple-500/20 transition-all active:scale-95 disabled:opacity-50"
            >
              📸 画面をキャプチャ
            </button>
          </div>
        </header>

        {/* Status Bar */}
        {status && (
          <div className={`p-4 rounded-xl border animate-in slide-in-from-top-2 duration-300 ${status.isError ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-green-500/10 border-green-500/30 text-green-500'
            }`}>
            <div className="flex items-center gap-3 text-sm font-medium">
              <span className={`w-2 h-2 rounded-full ${status.isError ? 'bg-red-500' : 'bg-green-500'} animate-pulse`}></span>
              {status.msg}
            </div>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-180px)]">
          {/* Left: Input Design */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-hidden">
            <section className="flex-1 bg-panel-bg backdrop-blur-md border border-panel-border rounded-3xl p-6 flex flex-col shadow-xl transition-colors">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-text-main">
                <span className="w-1.5 h-6 bg-purple-500 rounded-full"></span>
                AIへの指示
              </h2>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="flex-1 w-full bg-input-bg border border-input-border rounded-2xl p-4 text-text-main text-sm focus:ring-2 focus:ring-purple-500 outline-none transition-all resize-none font-mono"
                placeholder="どのようなシステムを作りますか？"
              />
              <button
                onClick={handleGenerate}
                disabled={isGenerating || cooldown > 0}
                className="w-full mt-4 py-4 bg-text-main text-app-bg font-black rounded-2xl transition-all hover:opacity-80 active:scale-95 shadow-xl shadow-black/5 disabled:opacity-50"
              >
                {isGenerating ? '生成中...' : cooldown > 0 ? `待機中 (${cooldown}s)` : 'システムを生成する'}
              </button>

              {isGenerating && (
                <div className="mt-6 p-4 bg-panel-bg border border-panel-border rounded-2xl animate-pulse">
                  <p className="text-[10px] text-text-sub font-bold uppercase mb-2">AIが考えたこと：</p>
                  <p className="text-xs text-text-sub italic">利用者様の意図を汲み取り、最適なテーブル構造を構築しています...</p>
                </div>
              )}

              {design?.thoughts && (
                <div className="mt-6 p-4 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
                  <p className="text-[10px] text-purple-400 font-bold uppercase mb-2 tracking-widest leading-loose">🎯 生成のポイント：</p>
                  <ul className="space-y-2">
                    {design.thoughts.map((thought, i) => (
                      <li key={i} className="text-xs text-text-sub flex gap-2">
                        <span className="text-purple-500">•</span>
                        {thought}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          </div>

          {/* Center: Schema Preview */}
          <div className="col-span-12 lg:col-span-6 flex flex-col gap-6 overflow-hidden">
            {design && (
              <div className="flex gap-4 p-1 bg-input-bg border border-panel-border rounded-2xl w-fit">
                <button
                  onClick={() => setViewMode('schema')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'schema' ? 'bg-text-main text-app-bg shadow-lg' : 'text-text-sub hover:text-text-main'}`}
                >
                  Schema
                </button>
                <button
                  onClick={() => setViewMode('layout')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'layout' ? 'bg-text-main text-app-bg shadow-lg' : 'text-text-sub hover:text-text-main'}`}
                >
                  Layout
                </button>
                <button
                  onClick={() => setViewMode('fixer')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'fixer' ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/20' : 'text-text-sub hover:text-text-main'}`}
                >
                  🔧 修整
                </button>
              </div>
            )}
            {!design && (
              <div className="flex gap-4 p-1 bg-input-bg border border-panel-border rounded-2xl w-fit">
                <button
                  onClick={() => setViewMode('fixer')}
                  className={`px-6 py-2 rounded-xl text-xs font-black tracking-widest uppercase transition-all ${viewMode === 'fixer' ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/20' : 'text-text-sub hover:text-text-main'}`}
                >
                  🔧 既存フィールド修整
                </button>
              </div>
            )}

            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {/* Schema View */}
              {viewMode === 'schema' ? (
                design ? (
                  <div className="space-y-6">
                    {(!design?.tables || design.tables.length === 0) ? (
                      <div className="bg-panel-bg backdrop-blur-md border border-panel-border rounded-3xl p-12 text-center text-text-sub">
                        <p className="text-xl font-bold">テーブル構造が見つかりませんでした</p>
                        <p className="text-sm mt-2">AIの出力を解析できませんでした。もう一度指示を変えて試してみてください。</p>
                      </div>
                    ) : (
                      design.tables.map((table) => (
                        <div key={table.name} className="bg-panel-bg backdrop-blur-md border border-panel-border rounded-3xl overflow-hidden shadow-2xl transition-colors">
                          <div className="bg-panel-bg p-6 flex justify-between items-center border-b border-panel-border">
                            <div>
                              <h3 className="text-2xl font-black text-purple-400">
                                {table.name}
                              </h3>
                              <p className="text-[10px] text-text-sub uppercase font-bold mt-1 tracking-widest">Database Table</p>
                            </div>
                            <div className="flex gap-3">
                              <button
                                onClick={() => copyToFM(generateFieldsXML(table.fields))}
                                className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/30 rounded-xl text-xs font-bold transition-all active:scale-95"
                              >
                                フィールドをコピー
                              </button>
                              <button
                                onClick={() => handleBatchCreateGUI(table.fields)}
                                className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 border border-indigo-500/30 rounded-xl text-xs font-bold transition-all active:scale-95"
                              >
                                一括GUI生成
                              </button>
                            </div>
                          </div>
                          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {table.fields.map((field) => (
                              <div key={field.name} className="group bg-input-bg border border-input-border p-4 rounded-2xl hover:border-purple-500/50 transition-all duration-300">
                                <div className="flex justify-between items-start mb-2">
                                  <span className="text-[10px] px-2 py-0.5 bg-panel-bg text-text-sub rounded-full font-bold uppercase border border-panel-border">
                                    {field.type}
                                  </span>
                                </div>
                                <div className="font-mono text-lg font-bold text-text-main group-hover:text-purple-400 transition-colors flex justify-between items-center">
                                  {field.name}
                                  <button
                                    onClick={() => handleCreateFieldGUI(field.name, field.type)}
                                    className="opacity-0 group-hover:opacity-100 p-1.5 bg-panel-bg hover:bg-white/20 rounded-lg transition-all text-[10px]"
                                    title="単体GUI作成"
                                  >
                                    🏗️
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                ) : currentFields.length > 0 ? (
                  <div className="space-y-6">
                    <div className="bg-panel-bg backdrop-blur-md border border-panel-border rounded-3xl overflow-hidden shadow-2xl transition-colors">
                      <div className="bg-panel-bg p-6 flex justify-between items-center border-b border-panel-border">
                        <div>
                          <h3 className="text-2xl font-black text-orange-400">
                            Current_Table
                          </h3>
                          <p className="text-[10px] text-text-sub uppercase font-bold mt-1 tracking-widest">Existing FileMaker Fields</p>
                        </div>
                        <p className="text-xs text-text-sub">{currentFields.length} fields loaded</p>
                      </div>
                      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {currentFields.map((field, i) => (
                          <div key={i} className="group bg-input-bg border border-input-border p-4 rounded-2xl hover:border-orange-500/50 transition-all duration-300">
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-[10px] px-2 py-0.5 bg-panel-bg text-text-sub rounded-full font-bold uppercase border border-panel-border">
                                {field.type}
                              </span>
                            </div>
                            <div className="font-mono text-lg font-bold text-text-main group-hover:text-orange-400 transition-colors">
                              {field.name}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-full bg-panel-bg border border-dashed border-panel-border rounded-3xl flex flex-col items-center justify-center p-12 text-text-sub">
                    <div className="text-8xl mb-6 opacity-20">📐</div>
                    <p className="text-xl font-bold opacity-40">設計案または既存フィールドがここに表示されます</p>
                    <p className="text-sm opacity-30 mt-2">左のパネルから指示を入力するか、修整タブから読み取ってください</p>
                  </div>
                )
              ) : viewMode === 'layout' ? (
                design && (
                  <div className="space-y-12 pb-20">
                    {design.layouts?.map((lyt: any, idx: number) => (
                      <div key={idx} className="bg-input-bg backdrop-blur-xl border border-input-border rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden group">
                        {/* Decorative Background */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-purple-500/10 to-indigo-500/10 blur-[100px] pointer-events-none" />

                        <div className="relative z-10">
                          <div className="flex justify-between items-start mb-10">
                            <div>
                              <h3 className="text-3xl font-black text-text-main tracking-tight">
                                {lyt.name}
                              </h3>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="px-3 py-1 bg-panel-bg rounded-full text-[10px] font-bold uppercase tracking-widest text-text-sub border border-panel-border">
                                  {lyt.type}
                                </span>
                                <span className="text-text-sub text-xs">for {lyt.table}</span>
                              </div>
                            </div>
                            <div className="flex gap-4 items-center">
                              <button
                                onClick={() => copyToFM(generateLayoutXML(lyt))}
                                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-2xl text-xs font-bold shadow-lg shadow-purple-500/20 transition-all active:scale-95"
                              >
                                レイアウトXMLをコピー
                              </button>
                              <div className="flex gap-2">
                                <div className="w-8 h-8 rounded-full shadow-inner border border-panel-border" style={{ backgroundColor: lyt.style?.primaryColor }}></div>
                                <div className="w-8 h-8 rounded-full shadow-inner border border-panel-border" style={{ backgroundColor: lyt.style?.accentColor }}></div>
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-12 gap-4 bg-panel-bg border border-input-border p-6 rounded-3xl min-h-[400px]">
                            {lyt.elements?.map((el: any, i: number) => (
                              <div
                                key={i}
                                style={{
                                  gridColumn: `span ${el.grid?.w || 4}`,
                                  gridRow: `span ${el.grid?.h || 1}`,
                                }}
                                className="bg-input-bg border border-input-border rounded-2xl p-4 hover:border-purple-500/30 transition-all group/el flex flex-col justify-center"
                              >
                                <label className="text-[10px] font-bold text-text-sub mb-1 uppercase tracking-tighter">
                                  {el.label}
                                </label>
                                <div className="h-10 bg-panel-bg rounded-lg border border-panel-border flex items-center px-4 text-xs text-text-sub italic">
                                  {el.field}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                    {(!design.layouts || design.layouts.length === 0) && (
                      <div className="h-64 flex flex-col items-center justify-center text-text-sub opacity-60">
                        <div className="text-6xl mb-4">✨</div>
                        <p className="text-xl font-bold italic text-center">
                          レイアウト案が生成されませんでした<br />
                          <span className="text-sm font-normal not-italic mt-2 block">指示を詳しくして再生成をお試しください</span>
                        </p>
                      </div>
                    )}
                  </div>
                )) : viewMode === 'fixer' ? (
                  <div className="space-y-6">
                    {/* Field Fixer Header */}
                    <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-3xl p-6">
                      <h3 className="text-xl font-black text-orange-400 mb-2">🔧 既存フィールド修整ツール</h3>
                      <p className="text-sm text-text-sub mb-4">FileMakerの既存フィールドを読み取り、AIが最適な名前・型を提案します。</p>

                      <div className="flex gap-3 flex-wrap">
                        <button
                          onClick={handleLoadCurrentFields}
                          disabled={isLoadingFields}
                          className="px-5 py-2 bg-panel-bg hover:bg-white/10 border border-panel-border rounded-xl text-sm font-bold transition-all disabled:opacity-50 text-text-main"
                        >
                          {isLoadingFields ? '読み取り中...' : '📥 フィールドを読み取る'}
                        </button>
                        <button
                          onClick={handleSuggestFixes}
                          disabled={isSuggesting || currentFields.length === 0}
                          className="px-5 py-2 bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/30 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                        >
                          {isSuggesting ? 'AI分析中...' : '🤖 AIに最適化してもらう'}
                        </button>
                      </div>
                    </div>

                    {/* Comparison Table */}
                    {suggestions.length > 0 && (
                      <div className="bg-input-bg border border-input-border rounded-3xl overflow-hidden">
                        <div className="grid grid-cols-12 gap-2 p-4 bg-panel-bg border-b border-panel-border text-[10px] font-bold uppercase tracking-widest text-text-sub">
                          <div className="col-span-4">現在のフィールド</div>
                          <div className="col-span-5">理想（AI提案）</div>
                          <div className="col-span-3 text-center">アクション</div>
                        </div>

                        <div className="divide-y divide-panel-border max-h-[400px] overflow-y-auto custom-scrollbar">
                          {suggestions.map((s, i) => (
                            <div key={i} className={`grid grid-cols-12 gap-2 p-4 items-center transition-all ${selectedFixes.has(i) ? 'bg-orange-500/10' : 'hover:bg-panel-bg'}`}>
                              <div className="col-span-4">
                                <div className="font-mono text-sm text-text-main">{s.old_name}</div>
                                <div className="text-[10px] text-text-sub">{s.old_type}</div>
                              </div>
                              <div className="col-span-5">
                                <div className={`font-mono text-sm ${s.old_name !== s.new_name ? 'text-green-500' : 'text-text-sub'}`}>
                                  {s.new_name}
                                </div>
                                <div className={`text-[10px] ${s.old_type !== s.new_type ? 'text-green-500' : 'text-text-sub'}`}>
                                  {s.new_type}
                                </div>
                                {s.comment && (
                                  <div className="text-[9px] text-text-sub mt-1 italic">{s.comment}</div>
                                )}
                              </div>
                              <div className="col-span-3 flex justify-center">
                                <button
                                  onClick={() => toggleFix(i)}
                                  className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${selectedFixes.has(i)
                                    ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                                    : 'bg-panel-bg text-text-sub hover:bg-white/10'
                                    }`}
                                >
                                  {selectedFixes.has(i) ? '✓ 修整' : 'スキップ'}
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Batch Fix Button */}
                        <div className="p-4 bg-panel-bg border-t border-panel-border flex justify-between items-center">
                          <div className="text-sm text-text-sub">
                            <span className="text-orange-400 font-bold">{selectedFixes.size}</span> 件を修整対象に選択中
                          </div>
                          <button
                            onClick={handleBatchFix}
                            disabled={isFixing || selectedFixes.size === 0}
                            className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-400 hover:to-red-400 text-white rounded-2xl font-bold shadow-lg shadow-orange-500/30 transition-all active:scale-95 disabled:opacity-50"
                          >
                            {isFixing ? '修整中...' : `🔧 ${selectedFixes.size}件を一括修整`}
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Current Fields List (before AI suggestions) */}
                    {currentFields.length > 0 && suggestions.length === 0 && (
                      <div className="bg-panel-bg backdrop-blur-md border border-orange-500/20 rounded-3xl overflow-hidden shadow-xl transition-colors">
                        <div className="bg-panel-bg p-4 flex justify-between items-center border-b border-panel-border">
                          <h4 className="text-sm font-bold text-orange-400">📥 読み取ったフィールド ({currentFields.length}件)</h4>
                          <div className="text-[10px] text-text-sub font-mono">Status: Ready to AI Analyze</div>
                        </div>
                        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[400px] overflow-y-auto custom-scrollbar">
                          {currentFields.map((f, i) => (
                            <div key={i} className="bg-input-bg border border-input-border p-3 rounded-xl flex justify-between items-center hover:border-orange-500/30 transition-all">
                              <span className="font-mono text-xs text-text-main truncate pr-2" title={f.name}>{f.name}</span>
                              <span className="text-[9px] text-text-sub bg-panel-bg px-2 py-0.5 rounded-full border border-panel-border whitespace-nowrap">{f.type}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
            </div>
          </div>
          {/* Right: Assets & History */}
          <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-hidden text-sm">
            <section className="flex-1 bg-panel-bg backdrop-blur-md border border-panel-border rounded-3xl p-6 flex flex-col shadow-xl overflow-hidden transition-colors">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-text-main">
                <span className="w-1.5 h-6 bg-pink-500 rounded-full"></span>
                キャプチャ履歴
              </h2>
              <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                {screenshots.length === 0 ? (
                  <div className="h-40 flex flex-col items-center justify-center text-text-sub opacity-60 italic">
                    画像がありません
                  </div>
                ) : (
                  screenshots.map((src, i) => (
                    <div key={i} className="group relative aspect-video bg-input-bg rounded-xl overflow-hidden border border-input-border hover:border-pink-500/50 transition-all cursor-pointer shadow-lg">
                      <img src={src} alt="Capture" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                        <span className="text-[10px] font-bold text-white truncate w-full">{src.split('/').pop()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(155, 155, 155, 0.2); 
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(155, 155, 155, 0.4);
        }
      `}</style>
    </main>
  );
}
