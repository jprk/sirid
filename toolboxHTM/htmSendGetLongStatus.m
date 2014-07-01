function htmSendGetLongStatus ( dataoutputstream, is_synchronous )
% R=HTMSENDGETLONGSTATUS(DOS,SYNC) sends "get_long_status" message to gantry server.
%
% Parameters:
%   dataoutputstream ... Java DataOutputStream instanace
%   is_synchronous ..... true if the future communication should be
%                        synchronous (gantry will block the microsimulator)
%
% See also
% http://iheartmatlab.blogspot.cz/2009/09/tcpip-socket-communications-in-matlab.html
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

    send_time = datestr(now,31);
    
    if is_synchronous
        synchronous = 'true';
    else
        synchronous = 'false';
    end
    
    % We need `sprintf()` call to implement the newline escape sequences,
    % as the standard string will contain literal '\' and 'n'.
    message = sprintf ([ ...
        '<?xml version="1.0" encoding="utf-8" ?>\n' ...
        '<gantry msg="get_long_status">\n' ...
        '  <datetime_format>YYYY-MM-DD hh:mm:ssZ</datetime_format>\n' ... 
        '  <send_time>' send_time '</send_time>\n' ... 
        '  <sender>MATLAB</sender>\n' ... 
        '  <receiver>Aimsun</receiver>\n' ...
        '  <transmission>tcp</transmission>\n' ... 
        '  <auth_code>Me be MOGAS! Me want data!</auth_code>\n' ... 
        '  <synchronous>' synchronous '</synchronous>\n' ...
        '</gantry>\n' ]);
    
    fprintf(1, 'Writing %d bytes\n', length(message))
    dataoutputstream.writeBytes(message);
    dataoutputstream.flush();

 % ----- END ( htmSetup ) -----