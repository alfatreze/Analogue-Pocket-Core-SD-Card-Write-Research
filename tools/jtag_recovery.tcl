# B005 held snapshots; no FPGA programming. Single-save pause points are explicit.
proc hex_number {raw} {regsub {^0[xX]} [string trim $raw] {} raw;if {![regexp {^[0-9a-fA-F]+$} $raw]} {error "Invalid hexadecimal value"};return [expr "0x$raw"]}
if {![info exists mode]} {set mode status}
if {![info exists point]} {set point 0}
if {$mode ni {status start cold pause resume results} || $point<0 || $point>3} {error "Invalid mode/point"}
set handle ""
foreach path [get_service_paths issp] {
 set candidate [claim_service issp $path ""];array unset info;array set info [issp_get_instance_info $candidate]
 if {$info(instance_name) eq "SDW5" && $info(source_width)==32 && $info(probe_width)==511} {
  if {$handle ne ""} {error "Ambiguous SDW5 instances"};set handle $candidate
 } else {close_service issp $candidate}
}
if {$handle eq ""} {error "Qualified SDW5 instance absent; do not program another core"}
set source [hex_number [issp_read_source_data $handle]]
proc snapshot {index} {
 global source handle
 set source [expr {($source&0xffffffc0)|$index}];issp_write_source_data $handle [format 0x%08x $source];after 5
 set source [expr {$source^0x80000000}];issp_write_source_data $handle [format 0x%08x $source]
 for {set attempt 0} {$attempt<20} {incr attempt} {
  after 5;set packet [hex_number [issp_read_probe_data $handle]];set header [expr {($packet>>448)&0xffffffff}]
  if {($header>>31)==($source>>31)} {
   set words {};for {set i 15} {$i>=0} {incr i -1} {lappend words [expr {($packet>>($i*32))&0xffffffff}]}
   if {[lindex $words 0]!=0x53445705 || (($header>>20)&255)!=0 || [lindex $words 2]!=$index} {error "B005 signature/revision/index mismatch"}
   return $words
  }
 }
 error "Snapshot handshake timed out"
}
set words [snapshot 0];set header [lindex $words 1]
set status [expr {($header>>16)&15}];set runmode [expr {($header>>28)&3}];set terminal [expr {($header>>30)&1}]
set state [expr {($header>>8)&255}];set reason [expr {$header&255}]
set formatted {};foreach w $words {lappend formatted [format %08x $w]}
puts "SDW5 summary words=[join $formatted ,]"
if {$mode in {start cold pause}} {
 if {$status!=0 || $state!=1 || [lindex $words 3]!=0 || [lindex $words 4]!=0} {error "Not fresh READY; never reset/retry live"}
 if {$mode eq "pause"} {
  set source [expr {($source&0xfffffcff)|0x08000000|($point<<8)}];issp_write_source_data $handle [format 0x%08x $source];after 5
 }
 set source [expr {$source^($mode eq "start"?0x40000000:$mode eq "cold"?0x20000000:0x10000000)}]
 issp_write_source_data $handle [format 0x%08x $source];puts "SDW5 requested $mode"
} elseif {$mode eq "resume"} {
 if {$status!=8 || $state!=14 || $runmode!=2 || $terminal} {error "Resume requires the explicit single-save pause state"}
 set source [expr {$source^0x04000000}];issp_write_source_data $handle [format 0x%08x $source];puts "SDW5 requested resume"
} elseif {$mode eq "results"} {
 if {$status ni {4 5 6 7} || !$terminal} {error "Results require finished state"}
 set count [expr {$runmode==1?0:[lindex $words 3]}]
 if {$count<0 || $count>64} {error "Invalid completed count"}
 for {set n 0} {$n<$count} {incr n} {set words [snapshot $n];set formatted {};foreach w $words {lappend formatted [format %08x $w]};puts "SDW5 record operation=$n words=[join $formatted ,]"}
}
close_service issp $handle;puts "SDW5 done"
