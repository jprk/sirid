function htmapiDemo()
%
% Demo application demonstrating how "toolboxHTM" can be used in
% collaboration with Aimsun micro simulator for simple highway traffic
% management tasks.
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 �VUT FD 
%
% Author: Jan P�ikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$


    fprintf ( '--------------------------------------------------------------------\n' );
    fprintf ( '  Demonstrator of HTM interface.\n' );
    fprintf ( '  This application demonstrates the process of collaboration between\n' );
    fprintf ( '  a hightway traffic management system and a microscopic traffic\n' );
    fprintf ( '  simulator.\n\n' );
    fprintf ( '  $Id$\n' );
    fprintf ( '--------------------------------------------------------------------\n' );
    fprintf ( '\n' );

    % Source the configuration file, providing SYSCONFIG structure.
    htmapi_config;
    
    % Extend the function search path to paths of HTM toolbox
    addpath ( SYSCONFIG.toolboxHTMdir );

    % Determine the proper architecture identifier for binaries.
    % Currently only `win32` and `x64` are supported.
    archStr = htmGetSystemArchitecture();
    
    % Add path to the place where possible DLLs reside
    addpath ( fullfile ( SYSCONFIG.toolboxHTMdir, archStr ));
    
    % Base path where scenarios are stored
    basePath = SYSCONFIG.aimsunScenariosDir;
    if ( basePath(end) ~= '\' && basePath(end) ~= '/' )
        basePath = [ basePath filesep ];
    end
    
    % Version string that is appended to files in .ang format
    if SYSCONFIG.aimsunVersion > 4
        versionStr = sprintf ( '_v%d', SYSCONFIG.aimsunVersion );
    else
        versionStr = '';
    end
    
    % Extract information about scenario and entrances
    scenario  = SYSCONFIG.scenarioName;
    entrances = SYSCONFIG.entrancesFileName;
    
    % If `entrances` is not empty, it points to a CSV file in the scenario
    % directory where traffic demand is stored.
    if ~isempty ( entrances )
        entrances = fullfile ( basePath, scenario, entrances );
    end
    
    % Remember the base path to scenario files. Extensions .sce/.ang and
    % .mat will be added later
    scenarioNoExt = fullfile ( basePath, scenario, scenario );
    scenarioNoExt = [ scenarioNoExt versionStr ];

    % Get the appropriate extension of the Aimsun scenario/project
    % file
    scenarioExt = '.sce';
    if SYSCONFIG.aimsunVersion > 4
        scenarioExt = '.ang';
    end
    
    % For Aimsun versions prior to 5 we have to modify the scenario file to
    % contain proper references to HTM Getram extensions. The call updates
    % also the name of the scenario file by appending 'htm'to the file
    % name.
    %
    % This is not necessary for Aimsun versions >= 5 as the scenario file
    % is a binary chunk that cannot be parsed and the AAPI extension files
    % (Python or binary DLLs) have to be injected using an initialisation
    % script written in Pythn.
    scenarioFullPath = [ scenarioNoExt scenarioExt ];
    if SYSCONFIG.aimsunVersion <= 4
        scenarioFullPath = ...
            htmUpdateScenarioDllPath ( scenarioFullPath, SYSCONFIG.getramHTMdll );
    
        % Make sure that the HTM communication library has been loaded.
        if ( ~htmInit ( archStr, SYSCONFIG.isDebugging ))
            error ( ...
                'sirid:interfrace:htmtoolbox', ...
                'htmInit() failed, cannot initialise `toolboxHTM`' );
        end
    end
    
    % Load network description XML file
    netInfo = htmLoadNetworkDescription ( [ scenarioNoExt '.xml' ] );
    
    % Specify files where sections and systems statistics will be written
    statsPrefix   = fullfile ( SYSCONFIG.reportDir, 'htmapiDemo' );
    sectionsStats = [ statsPrefix '_sections.csv' ];
    systemStats   = [ statsPrefix '_system.csv' ];
    
    % Set the simulation up.
    htmSetup ( ...
        entrances, ...
        netInfo.entranceSections, ...
        'HEADWAY_CONSTANT', ...
        sectionsStats, systemStats, ...
        netInfo.sections );
   
    % Connect to the gantry server
    htmConnect ( SYSCONFIG.htm_server, SYSCONFIG.htm_port );
    
    % --------------------
    % Create a default control action
    % --------------------
    gantry.id = 'R01-R-MX10042';    % Gantry server ID
    gantry.device = 1;              % The device on this gantry server
    gantry.symbol = 1;              % The symbol displayed
    gantry.validity = 60;           % The command will clear itself after 60 seconds
    control_set{1} = gantry;
    
    gantry.id = 'R01-R-MX10042';    % Gantry server ID
    gantry.device = 3;              % The device on this gantry server
    gantry.symbol = 1;              % The symbol displayed
    gantry.validity = 60;           % The command will clear itself after 60 seconds
    control_set{2} = gantry;

    % Cell vector that is used to collect raw statistics
    statCell = {};
    % Control loop result code is zero in case of a clean exit
    cl_res = 0;
    % The control loop loops forever
    k = 1;
    while ( true )
        
		fprintf ( '============================================================ STEP %d\n\n', k );

        % Step 1: Simulate computation of a control action
        fprintf ( ...
            '  %s Simulating computation of a new control action ...\n', ...
            datestr ( now, 13 ));
        pause ( 5 + round(rand(1)*5) );
        fprintf ( ...
            '  %s Sending the new control to controllers ...\n', ...
            datestr ( now, 13 ));

        % Step 2: Write the new control action to the microsimulator
        ct_res = htmWriteDataSet ( control_set );
        if ( ct_res ~= 0 )
            % Something bad happened.
			fprintf ( 'Error in htmWriteData() encountered. Exitting.\n' );
			break;
        end

        fprintf ( ...
            '  %s Written new control to the microsimulator\n', ...
            datestr ( now, 13 ));

        % Step 3: Wait for maximum one hour until data from the
        % microsimulator arrive 
		[ res, dets ] = htmWaitForData ( 3600, 1 );
        if ( res ~= 0 )
            % Something bad happened.
			fprintf ( 'Error in htmWaitForData() encountered. Exitting.\n' );
			break;
        end

        % Step 4: Process detector data
        % Loop over signal group data and show them
        fprintf ( ...
            '           Detected vehicle counts and occupancies:\n' );
        for i = 1:length(dets)
            dp = dets{i};
            fprintf ( '           %02d: gantry %s\n', i, dp.gantry_id );
            dd = dp.data;
            for j = 1:length(dd)
                % Fetch a single detecor record and show it
                dr = dd{j};
                fprintf ( ...
                    '               global time %6d --', ...
                    dr.global_time );
                fprintf ( ' %2d/%3d', [ dr.dt_intensity; dr.dt_occupancy] );
                fprintf ( '\n' );
            end
        end
        
        % Query the last section statistics from HTM toolbox
        stats = htmGetLastSectionStats();
        
        statCell{end+1} = stats;
        save ( 'stat_cell.mat', 'statCell' );

		k = k+1;
        fprintf ( '\n' );
    end
    
    % Wait for statistical data to be completely written to the disk
    if ( cl_res == 0 )
        res = htmWaitCompletedLoop ( 1200, 1 );
        if ( ~res )
            fprintf ( 'ERROR - Statistical data not available!\n' );
        end
    end
    fprintf ( ...
        '\n  %s Unloading the communication libraries ...\n', ...
        datestr ( now, 13 ));
    htmUnload ();
    fprintf ( 'htmapiDemo() finished.\n' );
    
end
    