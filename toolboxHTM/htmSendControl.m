function res=htmSendControl ( control_set )
% R=HTMSENDCONTROL(CS) sends a control set CS to the microsimulator.
%
% Parameters:
%   control_set ... a cell vector of control commands for gantries
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

global HTM_CONNECTION;
global HTM_PREFIX;

    res = 0;
    payload = '';
    for i = 1:length(control_set)
        gantry = control_set{i};
        command = sprintf ([ ...
            '  <gantry id="%s">\n' ...
            '    <device id="%d">\n' ...
            '      <subdevice id="%d">\n' ...
            '        <command validity="%d">\n' ...
            '          <symbol>%d</symbol>\n' ...
            '        </command>\n' ...
            '      </subdevice>\n' ...
            '    </device>\n' ...
            '  </gantry>\n' ], ...
            gantry.id, gantry.device, gantry.subdev, ...
            gantry.validity, gantry.symbol );
        payload = [ payload, command ];
    end
    
    % Send the payload
    % We need `sprintf()` call to implement the newline escape sequences,
    % as the standard string will contain literal '\' and 'n'.
    message = sprintf ([ ...
        '<?xml version="1.0" encoding="utf-8" ?>\n' ...
        '<root>\n' ...
        payload ...
        '</root>\n' ]);
    
    fprintf('%shtmSendControl() writing %d bytes\n', HTM_PREFIX, length(message))
    
    try
        HTM_CONNECTION.outputstream.writeBytes(message);
        HTM_CONNECTION.outputstream.flush();
    catch err
        err
        err.message
        err.stack
        res = -1;
    end
end
        
% ----- END ( htmSendControl ) -----