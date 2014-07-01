function ret = vgsWaitCompletedLoop ( numSeconds, verbose )
% R=VGSWAITCOMPLETEDLOOP(N) waits N seconds for statistical data.
%
% The function waits until all statistical data have been written to disk
% by the VGS API functions using wait steps of five seconds. The reason for
% this half-busy waiting is our concern of interuptibility of `calllib()`
% as the wait of, for example, 1200 seconds perfomed in `callib()` call
% may not be interruptible - this would block Matlab for twenty minutes in
% case of Aimsun misconfiguration, or could crash Matlab in `abort()` call
% when the VGS API DLL has been forced to unload.
%
% The returned value is Boolean - TRUE in case of a successful wait, FALSE
% in case of a timeout.
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsWaitCompletedLoop.m 1963 2008-04-07 14:31:23Z prikryl $
%

    % Check if the second parameter is present. If not, set output
    % verbosity to 0 (none).
    if ( nargin == 1 )
        verbose = 0;
    end
    
    % Initialise the return value
    ret = 0;
    
    % Half-busy wait for `numLoops` seconds.
    for i=1:numSeconds        
        ret = vgsWaitOnStatDataCompleted ( 1000 );
        if ( ret ), break, end
        if ( verbose )
            fprintf ( ...
                '  vgsWaitCompletedLoop(): timeout %5d of %5d\n', ...
                i, numSeconds );
        end
    end
    
% ----- END ( vgsWaitCompletedLoop ) -----