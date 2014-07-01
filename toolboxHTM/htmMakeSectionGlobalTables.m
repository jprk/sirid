function vgsMakeSectionGlobalTables ( statCell, titleCell, areaDescriptor, dirName, lang, tableType )
% VGSMAKESECTIONGLOBALTABLES(S,T,AD, D,LNG,TT) creates a tabular comparision of global section statistics.
%
% (c) 2008,2010 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeSectionGlobalTables.m 2723 2010-07-13 18:50:54Z prikryl $
%

    if nargin < 4
        tableType = 'latex';
    end
    
    % Number of `statCell` entries
    n = length ( statCell );

    % Number of sections
    sectionNameCell = areaDescriptor.Area.sectionNames;
    ns = length ( sectionNameCell );

    % Get legend descriptors
    [ statFieldNames, ...
      statFieldDesc, ...
      statFieldYLabels, ...
      statFieldUnits ] = vgsGetLegend ( 'globsection', lang );
    
    % Create directories
    dirPrefix = fullfile ( dirName, lang, 'tables' );
    [succ,mdg,msgid] = mkdir ( dirPrefix );

    for s=1:ns
        % Name of the section
        sn = sectionNameCell{s};
        
        % Skip elements that do not have a name
        if isempty ( sn ), continue, end;
        
        % Print the position in the section name vector
        fprintf ( '   Processing section ''%s'' (%d/%d) ', sn, s, ns );

        % Make the table
        if strcmp ( tableType, 'latex' )
            % Table file has to follow the TeX \input filename charset
            % limitation.
            sf = sprintf ( 'sectiontable_%02d.tex', s );
            % Try to open the output file.
            ofName = fullfile ( dirPrefix, sf );
            [of,emsg] = fopen ( ofName, 'w' );
            if of < 0
                error ( 'cannot open output file `%s`: %s', ofName, emsg );
            end
            % Message to the user
            fprintf ( ' file %s ', sf );
            % Determine the number of table columns holding real values and the
            % number of table columns holding the percentages (which will always be
            % one less than the number of real values)
            headStr = ',';
            valCols = repmat ( headStr, 1, n );
            pctCols = repmat ( headStr, 1, n-1 );
            % Open the tabular environment
            fprintf ( of, '%% ----------\n' );
            fprintf ( of, '%% Add the following three lines to the preamble:\n' );
            fprintf ( of, '%% \\usepackage{multirow}\n' );
            fprintf ( of, '%% \\usepackage{dcolumn}\n' );
            fprintf ( of, '%% \\newcolumntype{,}{D{,}{,}{-1}}\n' );
            fprintf ( of, '%% ----------\n' );
            fprintf ( of, '\\begin{tabular}{|l||%s|%s|}\n', valCols, pctCols );
            % Table head has two lines, this is the first one
            fprintf ( of, '\\hline\n' );
            for i = 1:n
                fprintf ( of, '& \\multicolumn{1}{c}{\\multirow{2}{*}{%s}} ', titleCell{i} );
            end
            for i = 2:n
                if i==2, c1='|'; else c1=''; end
                if i==n, c2='|'; else c2=''; end
                fprintf ( of, '& \\multicolumn{1}{%sc%s}{/%s} ', c1, c2, titleCell{i} );
            end
            fprintf ( of, '\\\\\n' );
            % Second line of table header does not contain the first `n` titles
            for i = 1:n
                fprintf ( of, '& \\multicolumn{1}{c}{} ' );
            end
            for i = 2:n
                if i==2, c1='|'; else c1=''; end
                if i==n, c2='|'; else c2=''; end
                fprintf ( of, '& \\multicolumn{1}{%sc%s}{/%s} ', c1, c2, titleCell{1} );
            end
            fprintf ( of, '\\\\\n' );
            fprintf ( of, '\\hline\n' );
            % Loop over all fields and create table rows for them
            for f = 1:length(statFieldNames)
                % Element name
                element = statFieldNames{f};
                % Element legend
                fprintf ( of, '%s %s ', statFieldDesc{f}, statFieldUnits{f} );
                % Data values
                for i = 1:n
                    % Convert decimal point to decimal comma
                    strNum = strrep ( sprintf ( '%6.2f', ...
                        statCell{i}.glob.( element )), '.', ',' );
                    % Fractional part of the value
                    fprintf ( of, '& %s ', strNum );
                end
                % Percentages
                for i = 2:n
                    pct = 100.0 * statCell{i}.glob.( element ) / ...
                          statCell{1}.glob.( element ) - 100.0;
                    % Convert decimal point to decimal comma
                    strNum = strrep ( sprintf ( '%5.1f', pct ), '.', ',' );
                    fprintf ( of, '& %s\\,\\%% ', strNum );
                end
                fprintf ( of, '\\\\\n' );
                % Write something to the terminal
                fprintf ( '.' );
            end
            % Close the tabular environment
            fprintf ( of, '\\hline\n' );
            fprintf ( of, '\\end{tabular}\n' );
            % Write a name of the section into the file.
            fprintf ( of, '%s', sn );
            fclose ( of );
            % Finish the line at the terminal.
            fprintf ( ' done.\n' );
        % HTML table
        elseif strcmp ( tableType, 'html' )
            of = fopen ( [ dirName '\globaltable.html' ], 'w' );
            % Table head
            fprintf ( of, '<table>\n', valCols, pctCols );
            % Table head
            fprintf ( of, '<tr>\n' );
            fprintf ( of, '  <th></th>\n' );
            for i = 1:n
                fprintf ( of, '  <th>%s</th>\n', titleCell{i} );
            end
            for i = 2:n
                fprintf ( of, '  <th>%s/%s</th>\n', titleCell{i}, titleCell{1} );
            end
            fprintf ( of, '</tr>\n' );
            % Loop over all fields and create table rows for them
            for f = 1:length(statFieldNames)
                % Element name
                element = statFieldNames{f};
                % Element legend
                fprintf ( of, '<tr>\n' );
                fprintf ( of, '  <td>%s %s</td>\n', statFieldDesc{f}, statFieldUnits{f} );
                % Data values
                for i = 1:n
                    fprintf ( of, '  <td>%6.2f</td>\n', statCell{i}.glob.( element ) );
                end
                % Percentages
                for i = 2:n
                    pct = statCell{i}.glob.( element )/statCell{1}.glob.( element )*100.0;
                    fprintf ( of, '  <td>%5.1f%%</td>\n', pct );
                end
                fprintf ( of, '<tr>\n' );
            end
            % Close the tabular environment
            fprintf ( of, '</table>\n' );
            fclose ( of );
        else
            error ( 'only latex or HTML output is supported' );
        end
    end
% ----- END ( vgsMakeSectionGlobalTables ) -----