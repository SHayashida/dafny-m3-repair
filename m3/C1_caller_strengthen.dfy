// ===== C1: caller強化 (Trend の requires を span>0 に強化) =====
// 契約項目: caller responsibility increased / caller admissible input narrowed
method Percent(part: int, whole: int) returns (r: int)
  requires whole > 0
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }

method Ratio(x: int) returns (r: int)
  ensures r == x * 100 / 4
{ r := Percent(x, 4); }

method Trend(delta: int, span: int) returns (r: int)
  requires span > 0                // ★ C1: span!=0 -> span>0 に強化
{ r := Percent(delta, span); }

// Trend の上流クライアント: C1で新たな証明義務が伝播するかのテスト
method TrendUserOK(d: int, s: int) returns (r: int)
  requires s > 0
{ r := Trend(d, s); }              // s>0 なのでOK

method TrendUserBROKEN(d: int, s: int) returns (r: int)
  requires s != 0
{ r := Trend(d, s); }              // ★ 連鎖失敗: span>0 を確立できない
