function vgsMakeCustomGraphs ( agType, statCell, titleCell, areaDescriptor, agPeriod, dirName, lang )
% VGSMAKECUSTOMGRAPHS(AGT,SC,TC,NC,AP,DN,LNG) produces comparative graphs of SC by custom aggregation type AGT.
%
% Parameters:
%   agType ........... code of the chosen custom aggregation type
%   statCell ......... aggregated statistical data for all sections in
%                      the network
%   titleCell ........ titles of particular channels (simulations) that
%                      will be displayed as graph legend
%   areaDescriptor ... description of the network we were simulating
%   agPeriod ......... aggregation period used to create `statCell` data
%   dirName .......... name od the base output directory
%   lang ............. language code ('cz' or 'en')
%
% (c) 2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeCustomGraphs.m 1963 2008-04-07 14:31:23Z prikryl $
%

    % Number of `statCell` entries
    n = length ( statCell );
    
    [ statFieldNames, ...
      statFieldDesc, ...
      statFieldYLabels, ...
      statFieldUnits, ...
      matchPos ] = vgsGetLegend ( agType, lang, areaDescriptor );
    
    colorMap = vgsGetColorMap ();
    
    nf = length ( statFieldNames );
    
    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\' agType '\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\' agType '\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\' agType '\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\' agType '\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    % Print the position in the section name vector
    fprintf ( '   Processing custom graph code ''%s'' ', agType );

    for f=1:nf
        % Element name
        element = statFieldNames{f};
        % Clear the figure window
        clf ( fh );
        sf = strrep ( agType, ' ', '_' );
        sf = strrep ( sf, '.', '_' );
        sf = strrep ( sf, '/', 'x' );
        fn = [ element '_' sf ];
        
        % Custom aggregation (the same code is also in
        % vgsMakeIntersectionGgraphs()).
        data = vgsAggregateSections ( statCell, element, areaDescriptor, matchPos );
        
        % Determine the data count
        dlen = length(statCell{1}.loc{1}.( element ));
        % Based on the aggregation period create the time values for x axis
        c = agPeriod / 86400;
        x = c * (0:(dlen-1));
        
        % Plot the bar graph, returning a vector of barseries objects
        h = bar ( x, data' );
        % Set colour of every bar series
        for j=1:n
            set ( h(j), 'FaceColor', colorMap(j,:));
        end
        % X axis time format
        datetick ( 'x', 15 );
        % X limits have to be slightly below minmum and sligntly above
        % maximum in order to accomodate all barseries
        xlim ( [ min(x)-c, max(x)+c ]);
        % Title, legend, axis description
        title ( [ ...
            areaDescriptor.Area.aggregationInfo.titleMap.(lang){matchPos} ...
            ] );
        legend ( titleCell );
        ylabel ( [ statFieldYLabels(f) statFieldUnits(f) ] );
        xlabel ( vgsTranslate('Time',lang) );
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
        % An now the same for absolute differences
        %
        rdata = zeros ( n-1, dlen);
        warning ( 'off', 'MATLAB:divideByZero' );
        for j=2:n
            rdata(j-1,:) = data(j,:) - data(1,:);
        end
        warning ( 'on', 'MATLAB:divideByZero' );
        h = bar ( x, rdata' );
        for j=2:n
            set ( h(j-1), 'FaceColor', colorMap(j,:));
        end
        % Dotted base line
        set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
        datetick ( 'x', 15 );
        xlim ( [ min(x)-c, max(x)+c ]);
        title ( [ ...
            areaDescriptor.Area.aggregationInfo.titleMap.(lang){matchPos}, ...
            vgsTranslate(' (difference)',lang) ...
            ] );
        legend ( titleCell{2:end} );
        ylabel ( [ ...
            statFieldYLabels{f} ...
            vgsTranslate('difference [%]',lang) ...
            ] );
        xlabel ( vgsTranslate('Time',lang) );
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
        rdata = zeros ( n-1, dlen);
        warning ( 'off', 'MATLAB:divideByZero' );
        for j=2:n
            rdata(j-1,:) = 100 * data(j,:) ./ data(1,:) - 100;
        end
        warning ( 'on', 'MATLAB:divideByZero' );
        h = bar ( x, rdata' );
        for j=2:n
            set ( h(j-1), 'FaceColor', colorMap(j,:));
        end
        % Dotted base line
        set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
        datetick ( 'x', 15 );
        xlim ( [ min(x)-c, max(x)+c ]);
        title ( [ ...
            areaDescriptor.Area.aggregationInfo.titleMap.(lang){matchPos}, ...
            vgsTranslate(' (relative)',lang) ...
            ] );
        legend ( titleCell{2:end} );
        ylabel ( [ ...
            statFieldYLabels{f} ...
            vgsTranslate('difference [%]',lang) ...
            ] );
        xlabel ( vgsTranslate('Time',lang) );
        %
        saveas ( fh, [ figDirPrefix 'r_' fn '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'r_' fn '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'r_' fn '.emf' ] );
        vgsSaveEPS ( fh, [ epsDirPrefix 'r_' fn '.eps' ], 'windows-1250' );
        %
        fprintf ( '.' );
        %
    end

    fprintf ( '\n' );    
    
% ----- END ( vgsMakeCustomGraphs ) -----