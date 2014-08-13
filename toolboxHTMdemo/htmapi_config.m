% This file has to follow the M-file syntax as it is being sourced
% by htmapiDemo code.

SYSCONFIG = struct();

% -------- Begin of user configurable part --------

% -------- Global parameters first

% If set to 1, Matlab will load the debug version of the API libraires
SYSCONFIG.isDebugging = 1;

% Name of the scenario to be simulated
SYSCONFIG.scenarioName = 'sokp';

% Version of Aimsun to use. This helps us to distringuish between
% version-depended parts of the code that support particular Aimsun version
% and also to distinguish between different scenario file names and format.
% Currently, Aimsun 4.x, 5.x, 6.x, 7.x and 8.x models should be supported
% but the support is not always thorougly tested.
SYSCONFIG.aimsunVersion = 7;
    
% Name of a CSV file containing vehicle entrance data for the current
% scenario. If the entrance data file name is empty, the predefined
% traffic demands from the scenaro will be used.
SYSCONFIG.entrancesFileName = [];

% Host name and port number of the SIRID Gantry server
SYSCONFIG.htm_server = '127.0.0.1';
SYSCONFIG.htm_port = 9999;

% -------- Platform-specific configuration
if ispc
    % Determine the drive letter (in case the code is installed on a portable
    % drive the drive letter may change on different computers)
    pth = fileparts ( mfilename('fullpath'));
    pfx = [ pth '\..' ];

    SYSCONFIG.toolboxHTMdir = [ pfx '\toolboxHTM' ];
    SYSCONFIG.getramHTMdll  = [ pfx '\getramExt_HTM\GetramHTM.dll' ];
    SYSCONFIG.aimsunScenariosDir = [ pfx ];
    SYSCONFIG.reportDir = [ 'C:\Users\Prikryl\Documents\Reports' ];

    clear pth dl pfx;
else
    % Unix configuration part
    pth = fileparts ( mfilename('fullpath'));
    dl  = '/home/hrsd';
    pfx = fullfile ( dl, '�TIA', 'Doprava-svn', 'AIMSUN-MATLAB' );

    SYSCONFIG.toolboxELS3dir = [ pfx '/toolboxELS3/trunk' ];
    SYSCONFIG.getramELS3dll  = [ pfx '/c-source/GetramExt_ELS3/trunk/GetramELS3.dll' ];
    SYSCONFIG.toolboxVGSdir  = [ pfx '/toolboxVGS/trunk' ];
    SYSCONFIG.getramVGSdll   = [ pfx '/c-source/GetramExt_VGS/trunk/GetramVGS.dll' ];
    SYSCONFIG.ASYNtoolboxDir = [ pfx '/toolboxASYN' ];
    SYSCONFIG.aimsunScenariosDir = [ pfx '/toolboxASYN/areas' ];
    SYSCONFIG.reportdir = fullfile ( dl, 'ÚTIA', 'Reports' );
    SYSCONFIG.momoIniDir = fullfile ( pth, 'data', 'momo' );

    clear pth dl pfx;
end

setpref('Internet','SMTP_Server','localhost');
setpref('Internet','E_mail','prikryl@fd.cvut.cz');

% -------- End of user configurable part --------