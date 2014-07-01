function msg = vgsTranslate ( msg, lang )
% MSG=VGSTRANSLATE(MSG,LNG) translated messages to given language.
%
% (c) 2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
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
                msg = 'Èas';
            case ' for intersection '
                msg = ' pro køiovatku ';
            case ' (relative)'
                msg = ' (relativní zmìny)';
            case ' (difference)'
                msg = ' (zmìny)';
            case 'difference [%]'
                msg = ' - rozdíl [%]';
            case 'difference'
                msg = 'rozdíl';
            case ' (whole network)'
                msg = ' (celá sí)';
            case ' (whole network, relative)'
                msg = ' (celá sí, relativní zmìny)';
            case ' (whole network, difference)'
                msg = ' (celá sí, rozdíly)';
            case ' for section '
                msg = ' pro sekci ';
            case 'Hourly average of maximum queue length [veh]'
                msg = 'Hodinové prùmìry maximální délky fronty [voz]';
            case 'Difference in maximum queue length [veh]'
                msg = 'Rozdíl v maximální délce fronty [voz]';
            case 'Relative difference in maximum queue length [%]'
                msg = 'Relativní zmìna maximální délky fronty [%]';
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