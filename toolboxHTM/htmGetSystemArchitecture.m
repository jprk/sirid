function archStr = htmGetSystemArchitecture()
%A=HTMGETSYSTEMARCHITECTURE() returns Windows compatible computer architecture string.
%
% Currently only win32 and x64 are supported.
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

    sysStr  = computer();
    switch sysStr
        case 'PCWIN'
            archStr = 'win32';
        case 'PCWIN64'
            archStr = 'x64';
        otherwise
        error ( ...
            'htmapi:system_architecture', ...
            'unsupported system architecture %s, only PCWIN and PCWIN64 supported', ...
            sysStr );
    end

% ----- END ( htmGetSystemArchitecture ) -----
