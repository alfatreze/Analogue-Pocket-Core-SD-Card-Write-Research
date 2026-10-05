# B004 SDW4 retained results; no FPGA programming or filesystem operations.
proc hex_number {raw} {
 regsub {^0[xX]} [string trim $raw] {} raw
 if {![regexp {^[0-9a-fA-F]+$} $raw]} {error "Invalid ISSP hexadecimal value"}
 return [expr "0x$raw"]
}
if {![info exists mode]} {set mode status}
if {$mode ni {status results start cold}} {error "Unknown mode"}
set handle ""
foreach path [get_service_paths issp] {
 set candidate [claim_service issp $path ""]
 array unset info
 array set info [issp_get_instance_info $candidate]
 if {$info(instance_name) eq "SDW4" && $info(source_width)==32 && $info(probe_width)==511} {
  if {$handle ne ""} {error "Ambiguous SDW4 instances"}
  set handle $candidate
 } else {close_service issp $candidate}
}
if {$handle eq ""} {error "Qualified SDW4 instance absent; do not program another core"}
set source [hex_number [issp_read_source_data $handle]]
proc snapshot {index} {
 global source handle
 set source [expr {($source&0xffffc000)|$index}]
 issp_write_source_data $handle [format 0x%08x $source]
 after 5
 set source [expr {$source^0x80000000}]
 issp_write_source_data $handle [format 0x%08x $source]
 for {set attempt 0} {$attempt<20} {incr attempt} {
  after 5
  set packet [hex_number [issp_read_probe_data $handle]]
  set header [expr {($packet>>448)&0xffffffff}]
  if {($header>>31)==($source>>31)} {
   set words {}
   for {set i 15} {$i>=0} {incr i -1} {lappend words [expr {($packet>>($i*32))&0xffffffff}]}
   if {[lindex $words 0]!=0x53445704 || (($header>>18)&255)!=2 || [lindex $words 2]!=$index} {error "B004 signature/revision/index mismatch"}
   return $words
  }
 }
 error "Snapshot handshake timed out"
}
set words [snapshot 0]
set header [lindex $words 1]
set status [expr {($header>>14)&15}]
set cold [expr {($header>>30)&1}]
set completed [lindex $words 3]
puts [format "SDW4 summary status=%d cold=%d terminal=%d completed=%d passed=%d failed=%d commands=%d first_failure=%d" $status $cold [expr {($header>>29)&1}] $completed [lindex $words 4] [lindex $words 5] [lindex $words 6] [expr {$header&16383}]]
if {$mode in {start cold}} {
 if {$status!=0 || $completed!=0 || [lindex $words 6]!=0} {error "Stress is not fresh READY; do not retry/reset live"}
 set source [expr {$source^($mode eq "start"?0x40000000:0x20000000)}]
 issp_write_source_data $handle [format 0x%08x $source]
 puts "SDW4 requested $mode"
} elseif {$mode eq "results"} {
 if {$status ni {4 5 7}} {error "Results require terminal stress state"}
 set count [expr {$status==7?$completed+1:($cold?32:10000)}]
 for {set n 0} {$n<$count} {incr n} {
  set index [expr {$cold?$n+((9999-$n)/32)*32:$n}]
  set words [snapshot $index]
  set formatted {}
  foreach w $words {lappend formatted [format %08x $w]}
  puts "SDW4 record operation=$index words=[join $formatted ,]"
 }
}
close_service issp $handle
puts "SDW4 done"
