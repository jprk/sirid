function vgsTest()
%
% Demo application demonstrating "toolboxVGS".
%
% (c) 2013 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: els3vgsDemo.m 2814 2010-09-09 15:06:35Z prikryl $


    fprintf ( '--------------------------------------------------------------------\n' );
    fprintf ( '  VGS interface demo.\n' );
    fprintf ( '  $Id: els3vgsDemo.m 2814 2010-09-09 15:06:35Z prikryl $\n' );
    fprintf ( '--------------------------------------------------------------------\n' );
    fprintf ( '\n' );

    % Source the configucation file, providing SYSCONFIG structure.
    vgs_config;
    
    % Create the Windows compatible architecture string, 'win32' or 'x64'
    % @TODO@
    
    % Extend the function search path to paths of ELS3 and VGS toolboxes
    addpath ( SYSCONFIG.toolboxVGSdir );
    addpath ( fullfile ( SYSCONFIG.toolboxVGSdir, 'x64' ));
    
    % Base path where scenarios are stored
    basePath = SYSCONFIG.aimsunScenariosDir;
    if ( basePath(end) ~= '\' && basePath(end) ~= '/' )
        basePath = [ basePath filesep ];
    end
    
    % Extract information about scenario and entrances
    scenario  = SYSCONFIG.scenarioName;
    entrances = SYSCONFIG.entrancesFileName;
    
    % Remember the base path to scenario files. Extensions .sce and .mat
    % will be added later
    scenarioNoExt = fullfile ( basePath, scenario, scenario );

    % Modify the scenario file to contain proper references to ELS3 and VGS
    % Getram extensions. Both calls update also the name of the scenario
    % file by appending 'els3' and 'vgs' to the file name.
    
    % Make sure that the VGS communication library has been loaded.
    if ( ~vgsInit (1))
        error ( ...
            'hrsd:interfrace:vgstoolbox', ...
            'vgsInit() failed, cannot initialise `toolboxVGS`' );
    end
    
    % Load scenario description file
    scInfo = load ( [ scenarioNoExt '.mat' ] );
    
    % Specify files where sections and systems statistics will be written
    statsPrefix   = fullfile ( SYSCONFIG.reportDir, 'vgsDemo' );
    sectionsStats = [ statsPrefix '_sections.csv' ];
    systemStats   = [ statsPrefix '_system.csv' ];
    
    vgsSetup ( ...
        fullfile ( basePath, scenario, entrances ), ...
        scInfo.Area.entranceSection, ...
        'HEADWAY_CONSTANT', ...
        sectionsStats, systemStats, ...
        scInfo.Area.sections );
    
    fprintf ( 'vgsSetup() finished, waiting ...\n' );

    res = vgsWaitCompletedLoop ( 1200, 1 );
    if ( ~res )
        fprintf ( 'ERROR - Statistical data not available!\n' );
    end

    fprintf ( ...
        '\n  %s Unloading the communication libraries ...\n', ...
        datestr ( now, 13 ));
    vgsUnload ();
    fprintf ( 'vgsDemo() finished.\n' );
    
end
