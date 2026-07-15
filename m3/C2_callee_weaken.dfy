// ===== C2: callee弱化 (Percent の requires を whole!=0 に弱化, 本体は不変) =====
// 契約項目: callee admissible input expanded / backward compatibility preserved
method Percent(part: int, whole: int) returns (r: int)
  requires whole != 0              // ★ C2: whole>0 -> whole!=0 に弱化
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }       // 本体は完全に不変（既に非ゼロ除数で全域）

method Ratio(x: int) returns (r: int)
  ensures r == x * 100 / 4
{ r := Percent(x, 4); }            // 既存クライアント: 壊れないことを確認

method Trend(delta: int, span: int) returns (r: int)
  requires span != 0               // 呼び手の契約は不変
{ r := Percent(delta, span); }     // span!=0 が弱化後の requires を満たす
