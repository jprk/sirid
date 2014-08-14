function htmapiDemo()
%
% Demo application demonstrating how "toolboxHTM" can be used in
% collaboration with Aimsun micro simulator for simple highway traffic
% management tasks.
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
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
        netInfo.sections, ...
        '           ' );
   
    % Connect to the gantry server
    htmConnect ( SYSCONFIG.htm_server, SYSCONFIG.htm_port );
    
    % --------------------
    % Create a default control action
    % --------------------
    gantry.id = 'R01-R-MX20017';    % Gantry server ID
    gantry.device = 1;              % The device on this gantry server
    gantry.subdev = 0;              % The sub-device on this gantry server
    gantry.symbol = 3;              % The symbol displayed
    gantry.validity = 60;           % The command will clear itself after 60 seconds
    control_set{1} = gantry;
    
    gantry.id = 'R01-R-MX20017';    % Gantry server ID
    gantry.device = 5;              % The device on this gantry server (speed limit)
    gantry.subdev = 0;              % The sub-device on this gantry server
    gantry.symbol = 3;              % The symbol displayed (80 km/h)
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

        % Step 1: Wait for maximum one hour until data from the
        % microsimulator arrive 
		% TODO: This is hardcoded, the `1` should be replaced by the
        % gantry server count
        [ res, dets ] = htmReceiveMeasurements(1);
        if ( res ~= 0 )
            if res == 1
                % Clean exit, Aimsun finished
                fprintf ( '  %s Simulation finished, exitting.\n', ...
                    datestr ( now, 13 ));
            else
                % Something bad happened.
                fprintf ( 'Error in htmReceiveMeasurements() encountered. Exitting.\n' );
                cl_res = 1;
            end
            break;
        end

        % Step 2: Process detector data
        % Loop over signal group data and show them
        dets_fieldnames = fieldnames(dets);
        num_gantry_servers = length(dets_fieldnames);
        fprintf ( ...
            '           Got data from %d gantry server(s).\n', num_gantry_servers );
        fprintf ( ...
            '           Detected vehicle counts, occupancies and speeds:\n' );
        for i = 1:num_gantry_servers
            gantry_server_id = dets_fieldnames{i};
            fprintf ( '             %02d: gantry %s\n', i, gantry_server_id );
            directions = dets.(gantry_server_id);
            for d = 1:2
                if d == 1
                    fprintf ( '                 left lanes:\n' );
                else
                    fprintf ( '                 right lanes:\n' );
                end
                % Fetch lane data in a single direction
                lanes = directions{d};
                for lane_idx = 1:length(lanes)
                    % Fetch a single direction
                    categories = lanes{lane_idx};
                    if ~isempty(categories)
                        fprintf ( '                   lane %02d\n', lane_idx );
                        for cn = 1:length(categories)
                            dd = categories(cn,:);
                            fprintf ( '                     cat %d - %2d/%6.2f/%6.2f\n', cn, dd );
                        end
                    end
                end
            end
        end
        
        % Step 3: Simulate computation of a control action based on the
        % received data
        fprintf ( ...
            '  %s Simulating computation of a new control action ...\n', ...
            datestr ( now, 13 ));
        pause ( 5 + round(rand(1)*5) );
        fprintf ( ...
            '  %s Sending the new control to controllers ...\n', ...
            datestr ( now, 13 ));

        % Step 4: Write the new control action to the microsimulator
        ct_res = htmSendControl ( control_set );
        if ( ct_res ~= 0 )
            % Something bad happened.
			fprintf ( 'Error in htmSendControl() encountered. Exitting.\n' );
			break;
        end

        fprintf ( ...
            '  %s Written new control to the microsimulator\n', ...
            datestr ( now, 13 ));

        
        % Query the last section statistics from HTM toolbox
        % stats = htmGetLastSectionStats();
        %
        % statCell{end+1} = stats;
        % save ( 'stat_cell.mat', 'statCell' );

		k = k+1;
        fprintf ( '\n' );
    end
    
    % Wait for statistical data to be completely written to the disk
    % if ( cl_res == 0 )
    if ( false )
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
    