// program_template.dfy
//
// Reference template documenting the source-generation semantics used by
// scripts/generate_dafny_variants.py. The generator fills the three
// parameterized slots below according to the retained lever set K.
//
// Retained-set convention: a lever KEPT => original commitment stays.
//   KEEP_TREND_NONZERO_DOMAIN         kept => {{TREND_REQ}} = "span != 0"
//                                     deleted (C1) => "span > 0"
//   KEEP_PERCENT_POSITIVE_PRECONDITION kept => {{PERCENT_REQ}} = "whole > 0"
//                                     deleted (C2) => "whole != 0"
//   KEEP_DIRECT_PERCENT_CALL          kept => {{TREND_BODY}} = direct call
//                                     deleted (C3) => guarded implementation
//
// Local scope emits Percent, Ratio, Trend.
// Closed-world scope additionally emits TrendUserOK and TrendUserNonzero.

method Percent(part: int, whole: int) returns (r: int)
  requires {{PERCENT_REQ}}
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }

method Ratio(x: int) returns (r: int)
  ensures r == x * 100 / 4
{ r := Percent(x, 4); }

method Trend(delta: int, span: int) returns (r: int)
  requires {{TREND_REQ}}
{{TREND_BODY}}

// --- closed-world scope only ---
// method TrendUserOK(d: int, s: int) returns (r: int)
//   requires s > 0
// { r := Trend(d, s); }
//
// method TrendUserNonzero(d: int, s: int) returns (r: int)
//   requires s != 0
// { r := Trend(d, s); }
