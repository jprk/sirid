function vgsUnload()
% VGSUNLOAD() unloads the vgs_api DLL
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsUnload.m 1963 2008-04-07 14:31:23Z prikryl $
%

    % If the library has been loaded already, get rid of it.
    if ( libisloaded ( 'vgs_api' ))
        unloadlibrary ( 'vgs_api' );
    end
  
% ----- END ( vgsUnload ) -----   