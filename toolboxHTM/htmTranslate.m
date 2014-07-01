function msg = vgsTranslate ( msg, lang )
% MSG=VGSTRANSLATE(MSG,LNG) translated messages to given language.
%
% (c) 2009 �TIA AV�R, v.v.i.
%
% Author: Jan P�ikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsTranslate.m 2671 2010-04-19 12:50:18Z prikryl $
%
global vgs_ignore_missing_translations;

    % Check the number of input parameters
    if nargin ~= 2
        error ( 'vgs:argin', ...
            'This function accepts two parameters.' );
    end
    
    if strcmp ( lang, 'en' )
        % Pass, the msg string is in English
    elseif strcmp ( lang, 'cs' )
        % Translate English to Czech
        switch ( msg )
            case 'Time'
                msg = '�as';
            case ' for intersection '
                msg = ' pro k�i�ovatku ';
            case ' (relative)'
                msg = ' (relativn� zm�ny)';
            case ' (difference)'
                msg = ' (zm�ny)';
            case 'difference [%]'
                msg = ' - rozd�l [%]';
            case 'difference'
                msg = 'rozd�l';
            case ' (whole network)'
                msg = ' (cel� s�)';
            case ' (whole network, relative)'
                msg = ' (cel� s�, relativn� zm�ny)';
            case ' (whole network, difference)'
                msg = ' (cel� s�, rozd�ly)';
            case ' for section '
                msg = ' pro sekci ';
            case 'Hourly average of maximum queue length [veh]'
                msg = 'Hodinov� pr�m�ry maxim�ln� d�lky fronty [voz]';
            case 'Difference in maximum queue length [veh]'
                msg = 'Rozd�l v maxim�ln� d�lce fronty [voz]';
            case 'Relative difference in maximum queue length [%]'
                msg = 'Relativn� zm�na maxim�ln� d�lky fronty [%]';
            otherwise
                if vgs_ignore_missing_translations
                    fprintf ([ ...
                        '<missing>\n' ...
                        'case ''%s''\n    msg = '' '';\n' ...
                        '</missing>\n' ], msg ); 
                else
                    error ( 'vgs:argerror', ...
                        [ 'No translation for template string ' ...
                          '"%s" to language "cs".' ], msg );
                end
        end
    else
        error ( 'vgs:langerror', ...
            'Wrong language code specified. Only "en" or "cs" allowed.' );
    end
            
% ----- END ( vgsGetLegend ) -----