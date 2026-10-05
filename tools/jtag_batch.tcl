# B003 ISSP access: no programming, no filesystem access from this script.
# Intel System Console, --script=<this-file> <status|results|start|cold>
proc hex_number {raw} {
    regsub {^0[xX]} [string trim $raw] {} raw
    if {![regexp {^[0-9a-fA-F]+$} $raw]} {error "Invalid ISSP hexadecimal value"}
    return [expr "0x$raw"]
}
if {![info exists mode]} {set mode [lindex $argv 0]}
if {$mode eq ""} {set mode status}
if {$mode ni {status results start cold}} {error "Use status, results, start or cold"}
set handle ""
foreach path [get_service_paths issp] {
    set candidate [claim_service issp $path ""]
    array unset info
    array set info [issp_get_instance_info $candidate]
    if {$info(instance_name) eq "SDW3" && $info(source_width)==32 && $info(probe_width)==256} {
        if {$handle ne ""} {error "Ambiguous SDW3 instances"}
        set handle $candidate
    } else {close_service issp $candidate}
}
if {$handle eq ""} {error "Qualified B003 SDW3 instance absent; do not program another core"}
set source [hex_number [issp_read_source_data $handle]]
proc snapshot {c ordinal} {
    global source handle
    set source [expr {($source & 0xffffff80) | (($ordinal-1)<<5) | $c}]
    issp_write_source_data $handle [format 0x%08x $source]
    after 5
    set source [expr {$source ^ 0x80000000}]
    issp_write_source_data $handle [format 0x%08x $source]
    for {set attempt 0} {$attempt<20} {incr attempt} {
        after 5
        set packet [hex_number [issp_read_probe_data $handle]]
        set header [expr {($packet>>192)&0xffffffff}]
        if {($header>>31)==($source>>31)} {
            set words {}
            for {set i 7} {$i>=0} {incr i -1} {
                lappend words [expr {($packet>>($i*32))&0xffffffff}]
            }
            if {[lindex $words 0]!=0x53445703} {error "B003 build signature mismatch"}
            if {(([lindex $words 1]>>14)&255) != 2} {error "B003R2 revision mismatch"}
            return $words
        }
    }
    error "Snapshot handshake timed out; no coherent result claimed"
}
set words [snapshot 0 1]
set status [expr {[lindex $words 1]&15}]
set counters [lindex $words 2]
puts [format "SDW3 summary status=%d cold=%d terminal=%d completed=%d passed=%d failed=%d commands=%d" \
    $status [expr {([lindex $words 1]>>30)&1}] [expr {([lindex $words 1]>>29)&1}] \
    [expr {$counters&255}] [expr {($counters>>8)&255}] \
    [expr {($counters>>16)&255}] [expr {($counters>>24)&255}]]
if {$mode in {start cold}} {
    if {$status!=0} {error "Batch is not READY; do not retry or reset live"}
    set source [expr {$source ^ ($mode eq "start" ? 0x40000000 : 0x20000000)}]
    issp_write_source_data $handle [format 0x%08x $source]
    puts "SDW3 requested $mode; capture retained results after completion"
} elseif {$mode eq "results"} {
    if {$status ni {4 5 7}} {error "Results require a completed or timed-out batch"}
    set cold [expr {([lindex $words 1]>>30)&1}]
    for {set c 0} {$c<32} {incr c} {
        set passes [expr {$c in {28 29} ? 3 : $c in {30 31} ? 2 : 1}]
        for {set p [expr {$cold?$passes:1}]} {$p<=$passes} {incr p} {
            set words [snapshot $c $p]
            set formatted {}
            foreach w $words {lappend formatted [format %08x $w]}
            puts "SDW3 record case=$c ordinal=$p words=[join $formatted ,]"
        }
    }
}
close_service issp $handle
exit 0
