function ret = vgsWaitOnStatDataCompleted ( timeout )
% R=VGSWAITONSTATDATACOMPLETED(T) waits T milliseconds on statistical data.
%
% The function waits until all statistical data have been written to disk
% by the VGS API functions. The returned value is of `eh_wres` type and has
% to be checked for two different possible exit conditions: data ready or
% timeout elapsed. 
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsWaitOnStatDataCompleted.m 1963 2008-04-07 14:31:23Z prikryl $
%

    ret = calllib ( 'vgs_api', 'vgs_wait_stats_complete', int32(timeout) );
    
% ----- END ( vgsWaitOnStatDataCompleted ) -----