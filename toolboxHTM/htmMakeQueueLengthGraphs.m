function vgsMakeQueueLengthGraphs ( statCell, legendCell, areaDescriptor, agPeriod, dirName, lang, filePrefix, graphType )
% VGSMAKEQUEUELENGTHGRAPHS(SC,LC,AD,AP,DN,LNG,PF,GT) produces comparative graphs of SC.
%
% Produces queue length comparisons based on data stored in cell vector SC.
% LC is a cell vector of legend strings describing experiments that
% produced data in SC. The lengths of SC and TC must therefore be equal. AD
% is the area desciptor structure that is typically stored as a .mat file
% in the Aimsun scenario directory under the same name as the scenario
% itself. AP is the aggregation period in seconds of data provided in SC.
% Aggregation period is used to determine the values on time axis. DN is
% the full path to the base directory where results shall be stored. The
% function will create directories '<DN>\queues\fig', '<DN>\queues\png',
% '<DN>\queues\eps' and '<DN>\queues\emf'. FP is a string with file prefix
% assigned to each file, forming file names composed of prefix, section
% name and lane number in the form of
% '<FP><downstream_section_name><lane_id>.{png,eps,fig}'. GT is  a string
% denoting the graph type, either 'line' or 'bar'.
%
% (c) 2008,2009,2010 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeQueueLengthGraphs.m 2738 2010-07-29 14:46:11Z prikryl $

% Output file prefixes determine also the title of the graph
PREFIXES = {
    'qmaxl',
    'qmaxs',
    'qmaxm',
    'qtotl',
    'qtots',
    'qtotm'
    };

% Allowed graph types
GRAPHS = { 'line', 'bar' };

    % Check the number of parameters
    if ( nargin ~= 8 )
        error ( 'vgs:numargs', 'Function expects 8 parameters.' );
    end

    % Find out which from the allowed set of parameters has been chosen
    fpIndex = strcmp ( filePrefix, PREFIXES );
    if ( sum ( fpIndex ) ~= 1 )
        error ( 'vgs:argerror', 'Wrong file prefix.' );
    end
    
    % Check the graph type
    graphIndex = strcmp ( graphType, GRAPHS );
    if ( sum ( graphIndex ) ~= 1 )
        error ( 'vgs:argerror', 'Wrong graph type.' );
    end
    
    % Graph titles corresponding to the list of prefixes
    if strcmp ( lang, 'en' )
        titles = {{
        'Maximum simulated lane queue', ...
        'Maximum simulated section queue', ...
        'Maximum modelled lane queue', ...
        'Total of simulated lane queues', ...
        'Total of simulated section queues', ...
        'Total of modelled lane queues'
        },{
        'Averaged maximum of simulated lane queue', ...
        'Averaged maximum simulated section queue', ...
        'Averaged maximum modelled lane queue', ...
        'Averaged total of simulated lane queues', ...
        'Averaged total of simulated section queues', ...
        'Averaged total of modelled lane queues'
        }};
    elseif strcmp ( lang, 'cs' )
        titles = {{
        'Maximální simulovaná fronta po pruzích', ...
        'Maximální simulovaná fronta po sekcích', ...
        'Maximální modelovaná fronta po pruzích', ...
        'Souèet maximálnách simulovaných front po pruzích', ...
        'Souèet maximálnách simulovaných front po sekcích', ...
        'Souèet maximálnách modelovaných front po pruzích'
        },{
        'Averaged maximum of simulated lane queue', ...
        'Averaged maximum simulated section queue', ...
        'Averaged maximum modelled lane queue', ...
        'Averaged total of simulated lane queues', ...
        'Averaged total of simulated section queues', ...
        'Averaged total of modelled lane queues'
        }};
    else
        error ( 'vgs:argerror', 'Wrong language type.' );
    end

    % Retrieve the graph title
    graphTitle = titles{graphIndex}{fpIndex};
    
    % Number of `statCell` entries
    n = length ( statCell );
    
    % Number of rows in a `statCell` entry
    nd = size ( statCell{1}, 1 );
    
    % Number of sections
    sectionNameCell = areaDescriptor.Area.sectionNames;
    
    % Number of queues. The queue name map has two columns: the index in
    % the first column corresponds to the string in `sectionNameCell` and
    % denotes lane name. However, in some cases we have more lanes in a
    % signle section. Hence the second column, which contains lane index
    % for the given lane.
    queueNameMap = areaDescriptor.Area.queueMap.sectionIndexes;
    nq = size ( queueNameMap, 1 );

    % Number of queues should correspond to the number of `statCell` rows.
    % The only exception is the graph of totals - that graph has just a
    % single data row and the file prefix should contain 'tot' as a
    % substring.
    if ( nd ~= nq )
        if ( nd == 1 && strcmp ( filePrefix(2:4), 'tot' ))
            nq = 1;
            queueNameMap = [];
        else
            error ( 'vgs:argerror', ...
                'Number of queues in the data differs from that given by area descriptor.' );
        end
    end
    % Number of time slots in the bar graph
    nt = size ( statCell{1}, 2 );
    
    % Color map for the graph
    colorMap = vgsGetColorMap ();

    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\queues\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\queues\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\queues\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\queues\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    % Loop over all queues
    for qi = 1:nq
        
        % Section name for this queue
        if ( isempty ( queueNameMap ))
            qn = 'whole network';
        else
            qn = [ ...
            sectionNameCell{queueNameMap(qi,1)} ...
            ' lane ' ...
            num2str(queueNameMap(qi,2)) ];
        end
        
        % Clear the figure window
        clf ( fh );
        sf = strrep ( qn, ' ', '_' );
        sf = strrep ( sf, '.', '_' );
        fn = [ filePrefix '_' sf ];

        fprintf ( '   Processing queue ''%s'' (%d/%d): ', qn, qi, nq );

        % Allocate data matrix for the bar graph, representing `n`
        % experiments and `nt` time slots
        data = zeros ( n, nt );
    
        for j = 1:n
            data(j,:) = statCell{j}(qi,:);
        end

        % Based on the aggregation period create the time values for x axis
        c = agPeriod / 86400;
        x = c * (0:(nt-1));
        % We have possibility of different graph types
        switch graphType
            case 'bar'
                % Plot the bar graph, returning a vector of barseries objects
                h = bar ( x, data' );
                % Set colour of every bar series
                for j=1:n
                    set ( h(j), 'FaceColor', colorMap(j,:));
                end
            case 'line'
                % Plot the bar graph, returning a vector of barseries objects
                h = plot ( x, data' );
                % Set colour of every lineseries object
                for j=1:n
                    set ( h(j), 'Color', colorMap(j,:));
                end
            otherwise
                error ( 'vgs:argerror', 'Wrong graph type.' );
        end
        % X axis time format
        datetick ( 'x', 15 );
        % X limits have to be slightly below minmum and sligntly above
        % maximum in order to accomodate all barseries
        xlim ( [ min(x)-c, max(x)+c ]);
        % Graph description
        title ({ graphTitle ; qn });
        ylabel ( vgsTranslate ( ...
            'Hourly average of maximum queue length [veh]', lang  ));
        xlabel ( vgsTranslate ( 'Time', lang ));
        legend ( legendCell );
        %
        set ( fh, 'PaperUnits', 'centimeters' );
        set ( fh, 'PaperSize', [15,10] );
        set ( fh, 'PaperPositionMode', 'manual' );
        set ( fh, 'PaperPosition', [0,0,15,10] );
        %
        saveas ( fh, [ figDirPrefix 'a_' fn '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'a_' fn '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'a_' fn '.emf' ] );
        vgsSaveEPS ( fh, [ epsDirPrefix 'a_' fn '.eps' ], 'windows-1250' );
        %
        fprintf ( '.' );
        %
        % An the same for differences
        %
        rdata = zeros ( n-1, nt);
        for j=2:n
            rdata(j-1,:) = data(j,:) - data(1,:);
        end
        % We have possibility of different graph types
        switch graphType
            case 'bar'
                % Plot the bar graph, returning a vector of barseries objects
                h = bar ( x, rdata' );
                % Set colour of every bar series
                for j=2:n
                    set ( h(j-1), 'FaceColor', colorMap(j,:));
                end
                % Dotted base line
                set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
            case 'line'
                % Plot the bar graph, returning a vector of barseries objects
                h = plot ( x, data' );
                % Set colour of every lineseries object
                for j=2:n
                    set ( h(j-1), 'Color', colorMap(j,:));
                end
            otherwise
                error ( 'vgs:argerror', 'Wrong graph type.' );
        end
        % X axis time format
        datetick ( 'x', 15 );
        % X limits have to be slightly below minmum and sligntly above
        % maximum in order to accomodate all barseries
        xlim ( [ min(x)-c, max(x)+c ]);
        % Graph description
        title ({ graphTitle ; qn });
        ylabel ( vgsTranslate ( ...
            'Difference in maximum queue length [veh]', lang ));
        xlabel ( vgsTranslate ( 'Time', lang ));
        legend ( legendCell{2:end} );
        %
        set ( fh, 'PaperUnits', 'centimeters' );
        set ( fh, 'PaperSize', [15,10] );
        set ( fh, 'PaperPositionMode', 'manual' );
        set ( fh, 'PaperPosition', [0,0,15,10] );
        %
        saveas ( fh, [ figDirPrefix 'd_' fn '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'd_' fn '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'd_' fn '.emf' ] );
        vgsSaveEPS ( fh, [ epsDirPrefix 'd_' fn '.eps' ], 'windows-1250' );
        %
        fprintf ( '.' );
        %
        % An now the same for relative improvements
        %
        rdata = zeros ( n-1, nt );
        warning ( 'off', 'MATLAB:divideByZero' );        for j=2:n
            rdata(j-1,:) = 100 * data(j,:) ./ data(1,:) - 100 ;
        end
        warning ( 'on', 'MATLAB:divideByZero' );
        % We have possibility of different graph types
        switch graphType
            case 'bar'
                % Plot the bar graph, returning a vector of barseries objects
                h = bar ( x, rdata' );
                % Set colour of every bar series
                for j=2:n
                    set ( h(j-1), 'FaceColor', colorMap(j,:));
                end
                % Dotted base line
                set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
            case 'line'
                % Plot the bar graph, returning a vector of barseries objects
                h = plot ( x, data' );
                % Set colour of every lineseries object
                for j=2:n
                    set ( h(j-1), 'Color', colorMap(j,:));
                end
            otherwise
                error ( 'vgs:argerror', 'Wrong graph type.' );
        end
        % X axis time format
        datetick ( 'x', 15 );
        % X limits have to be slightly below minmum and sligntly above
        % maximum in order to accomodate all barseries
        xlim ( [ min(x)-c, max(x)+c ]);
        % Graph description
        title ({ graphTitle ; qn });
        ylabel ( vgsTranslate ( ...
            'Relative difference in maximum queue length [%]', lang ));
        xlabel ( vgsTranslate ( 'Time', lang ));
        legend ( legendCell{2:end} );
        %
        set ( fh, 'PaperUnits', 'centimeters' );
        set ( fh, 'PaperSize', [15,10] );
        set ( fh, 'PaperPositionMode', 'manual' );
        set ( fh, 'PaperPosition', [0,0,15,10] );
        %
        saveas ( fh, [ figDirPrefix 'r_' fn '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'r_' fn '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'r_' fn '.emf' ] );
        vgsSaveEPS ( fh, [ epsDirPrefix 'r_' fn '.eps' ], 'windows-1250' );
        %
        fprintf ( '. finished.\n' );
    end
    
% ----- END ( vgsMakeQueueLengthGraphs ) -----