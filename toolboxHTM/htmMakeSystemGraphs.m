function vgsMakeSystemGraphs ( statCell, titleCell, dirName, lang )
% VGSMAKESYSTEMGRAPHS(SC,TC,DN,LNG) produces comparative system graphs of SC.
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeSystemGraphs.m 2677 2010-04-27 15:32:49Z prikryl $
%

    % Number of `statCell` entries
    n = length ( statCell );
    
    % Check the compatibility of all `statCell` entries with respect to the
    % aggregation data.
    aggregation = statCell{1}.aggregation;
    if n > 2
        for ii=2:n
            % Function `isequal()` checks if arrays are equal
            if ~isequal ( aggregation, statCell{ii}.aggregation )
            error ( 'vgs:aggregation', ...
                [ 'The aggregation records at positions 1 and %d of the first cell\n' ...
                  'array argument differ, which suggests that the data is incompatible.\n' ], ii );
            end
        end
    end
    
    % At the present moment we can handle only uniform aggregation, that
    % means that the `aggregation` array has to be scalar.
    if ~isscalar ( aggregation )
        error ( 'vgs:aggregation', ...
            'Cannot handle non-scalar agregation yet.' );
    else
        agPeriod = aggregation;
    end
    
    % Get all the legend strings localised.
    [ statFieldNames, ...
      statFieldDesc, ...
      statFieldYLabels, ...
      statFieldUnits ] = vgsGetLegend ( 'system', lang );
    
    colorMap = vgsGetColorMap ();
    
    % Number of statistics that are stored in cell arrays
    nf = length ( statFieldNames );
    
    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\system\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\system\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\system\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\system\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    % Print something to the console
    fprintf ( '   Processing graphs for the whole system: ' );
    
    for f=1:nf
        % Element name
        element = statFieldNames{f};
        % Clear the figure window
        clf ( fh );
        % Determine the data count
        dlen = length(statCell{1}.loc.( element ));
        % If dlen == 1 the resulting data matrix will degrate to a vector
        % and the `bar()` function will not work properly. Exit now.
        if ( dlen <= 1 )
            fprintf ( '\n' );
            error ( 'vgs:datalen', ...
                [ 'Data length for statistical field "%s" is less than two.\n' ...
                  'This will crash the bar() routine that produces our graphs.\n' ...
                  'Please, decrease the aggregation period of your data to be\n' ...
                  'at most the half of your simulation period.\n' ], element );
        end
        % Allocate data matrix for the bar graph
        data = zeros ( n, dlen );
        for j=1:n
            data(j,:) = statCell{j}.loc.( element );
        end
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
        title ([ ...
            statFieldDesc{f} ...
            vgsTranslate(' (whole network)',lang) ...
            ]);
        legend ( titleCell );
        ylabel ( [ statFieldYLabels{f} statFieldUnits{f} ] );
        xlabel ( vgsTranslate ( 'Time', lang ));
        %
        set ( fh, 'PaperUnits', 'centimeters' );
        set ( fh, 'PaperSize', [15,10] );
        set ( fh, 'PaperPositionMode', 'manual' );
        set ( fh, 'PaperPosition', [0,0,15,10] );
        %
        saveas ( fh, [ figDirPrefix 'a_' element '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'a_' element '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'a_' element '.emf' ] );
        saveas ( fh, [ epsDirPrefix 'a_' element '.eps' ], 'epsc' );
        %
        fprintf ( '.' );
        %
        % An the same for differences
        %
        rdata = zeros ( n-1, dlen);
        for j=2:n
            rdata(j-1,:) = data(j,:) - data(1,:);
        end
        h = bar ( x, rdata' );
        for j=2:n
            set ( h(j-1), 'FaceColor', colorMap(j,:));
        end
        % Dotted base line
        set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
        datetick ( 'x', 15 );
        xlim ( [ min(x)-c, max(x)+c ]);
        title ([ ...
            statFieldDesc{f} ...
            vgsTranslate(' (whole network, difference)',lang) ...
            ]);
        legend ( titleCell{2:end} );
        ylabel ([ ...
            statFieldYLabels{f} ...
            vgsTranslate('difference',lang) ' ' ...
            statFieldUnits{f} ...
            ]);
        xlabel ( vgsTranslate ( 'Time', lang ));
        %
        saveas ( fh, [ figDirPrefix 'd_' element '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'd_' element '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'd_' element '.emf' ] );
        saveas ( fh, [ epsDirPrefix 'd_' element '.eps' ], 'epsc' );
        %
        fprintf ( '.' );
        %
        %
        % An now the same for relative improvements
        %
        rdata = zeros ( n-1, dlen);
        for j=2:n
            % rdata(j-1,:) = 100 * data(j,:) ./ data(1,:);
            rdata(j-1,:) = 100 * data(j,:) ./ data(1,:) - 100 ;
        end
        h = bar ( x, rdata' );
        for j=2:n
            set ( h(j-1), 'FaceColor', colorMap(j,:));
        end
        % Dotted base line
        set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
        datetick ( 'x', 15 );
        xlim ( [ min(x)-c, max(x)+c ]);
        title ([ statFieldDesc{f} ' (whole network, relative)' ] );
        legend ( titleCell{2:end} );
        ylabel ([ ...
            statFieldYLabels{f} ...
            vgsTranslate('difference [%]',lang) ...
            ]);
        xlabel ( vgsTranslate ( 'Time', lang ));
        %
        saveas ( fh, [ figDirPrefix 'r_' element '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'r_' element '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'r_' element '.emf' ] );
        saveas ( fh, [ epsDirPrefix 'r_' element '.eps' ], 'epsc' );
        %
        fprintf ( '.' );
        %
    end
    fprintf ( '\n' );
    
% ----- END ( vgsMakeSystemGraphs ) -----