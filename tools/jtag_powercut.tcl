# B007R1 SDW7 read-only snapshot and bounded observer. Never controls the core.
proc hex_number {raw} {
 regsub {^0[xX]} [string trim $raw] {} raw
 if {![regexp {^[0-9a-fA-F]+$} $raw]} {error "Invalid hexadecimal value"}
 return [expr "0x$raw"]
}
if {![info exists mode]} {set mode status}
if {![info exists duration]} {set duration 300}
if {![info exists poll_ms]} {set poll_ms 25}
if {$mode ni {status results monitor} || $duration<1 || $duration>1800 || $poll_ms<10 || $poll_ms>1000} {
 error "Invalid read-only observer mode or bounds"
}
set handle ""
foreach path [get_service_paths issp] {
 set candidate [claim_service issp $path ""]
 array unset info
 array set info [issp_get_instance_info $candidate]
 if {$info(instance_name) eq "SDW7" && $info(source_width)==32 && $info(probe_width)==511} {
  if {$handle ne ""} {error "Ambiguous SDW7 instances"}
  set handle $candidate
 } else {close_service issp $candidate}
}
if {$handle eq ""} {error "Qualified SDW7 instance absent; do not program another core"}
set source [hex_number [issp_read_source_data $handle]]
proc snapshot {} {
 global source handle
 set source [expr {($source&0xffffffc0)}]
 issp_write_source_data $handle [format 0x%08x $source]
 after 3
 set source [expr {$source^0x80000000}]
 issp_write_source_data $handle [format 0x%08x $source]
 for {set attempt 0} {$attempt<30} {incr attempt} {
  after 2
  set packet [hex_number [issp_read_probe_data $handle]]
  set header [expr {($packet>>448)&0xffffffff}]
  if {($header>>31)==($source>>31)} {
   set words {}
   for {set i 15} {$i>=0} {incr i -1} {lappend words [expr {($packet>>($i*32))&0xffffffff}]}
   if {[lindex $words 0]!=0x53445707 || [lindex $words 14]!=65536 || [lindex $words 15]!=0} {
    error "SDW7 signature/length mismatch"
   }
   return $words
  }
 }
 error "SDW7 snapshot handshake timed out"
}
proc format_words {words} {
 set formatted {}
 foreach word $words {lappend formatted [format %08x $word]}
 return [join $formatted ,]
}
set words [snapshot]
puts "SDW7 summary words=[format_words $words]"
if {$mode eq "monitor"} {
 set started [clock milliseconds]
 set sample 0
 while {[clock milliseconds]-$started < $duration*1000} {
  after $poll_ms
  if {[catch {set words [snapshot]} err]} {
   puts "SDW7 link-lost sample=$sample error=$err"
   break
  }
  puts "SDW7 sample n=$sample elapsed_ms=[expr {[clock milliseconds]-$started}] words=[format_words $words]"
  incr sample
 }
 puts "SDW7 monitor-ended samples=$sample"
}
catch {close_service issp $handle}
puts "SDW7 done"
