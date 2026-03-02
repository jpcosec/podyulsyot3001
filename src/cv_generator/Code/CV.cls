%                                           ,,                       ,,                       
%   .g8"""bgd                                db                     `7MM
% .dP'     `M                                                         MM                                                
% dM'       ``7MM  `7MM  `7Mb,od8 `7Mb,od8 `7MM  ,p6"bo `7MM  `7MM    MM `7MM  `7MM  `7MMpMMMb.pMMMb. 
% MM           MM    MM    MM' "'   MM' "'   MM 6M'  OO   MM    MM    MM   MM    MM    MM    MM    MM
% MM.          MM    MM    MM       MM       MM 8M        MM    MM    MM   MM    MM    MM    MM    MM 
% `Mb.     ,'  MM    MM    MM       MM       MM YM.    ,  MM    MM    MM   MM    MM    MM    MM    MM  
%   `"bmmmd'   `Mbod"YML..JMML.   .JMML.   .JMML.YMbmd'   `Mbod"YML..JMML. `Mbod"YML..JMML  JMML  JMML.
%
%
% `7MMF'   `7MF'db   mm                   
%   `MA     ,V       MM                   
%    VM:   ,V `7MM mmMMmm  ,6"Yb.  .gP"Ya 
%     MM.  M'   MM   MM   8)   MM ,M'   Yb
%     `MM A'    MM   MM    ,pm9MM 8M""""""
%      :MM;     MM   MM   8M   MM YM.    ,
%       VF    .JMML. `Mbmo`Moo9^Yo.`Mbmmd'
%
%---------------------------------------------------------------------------------------------------------------------
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% *** LaTeX-class for Curriculum Vitae (CV), 
%
%                           V.01.0 // Version 01, with 0 update(s) or patch(es)
%
% First released January 2023. 
% Last updated January 2023.
%
%---------------------------------------------------------------------------------------------------------------------
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%                   Defining the .cls file
%_______________________________________________________________
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{Code/CV}[2023/01/13 Curriculum Vitae]
\LoadClass[a4paper,9pt]{extarticle} % Base class (extarticle supports 9pt)
\RequirePackage[utf8]{inputenc}
%................................................................
%
%                           Options
%_______________________________________________________________
% Handling of mutually exclusive options:
%-------------------------------
\chardef\photo@optA=0
\chardef\photo@optB=0
%
\chardef\header@optA=0
\chardef\header@optB=0
\chardef\header@optC=0
%
\chardef\name@optA=0
\chardef\name@optB=0
\chardef\name@optC=0
\chardef\name@optD=0
\chardef\name@optE=0
%
\chardef\bib@optA=0
\chardef\bib@optB=0
\chardef\bib@optC=0
\chardef\bib@optD=0
\chardef\bib@optE=0
%
% Photo options:
%-------------------------------
% No photo:
\newif\if@nophoto
\DeclareOption{nophoto}{\@nophototrue \chardef\photo@optA=1\relax}
% No photo, centered text:
\newif\if@centered
\DeclareOption{nophotocenter}{\@centeredtrue \@nophototrue}
% Photo on the left side, text on the right:
\newif\if@photoleft
\newif\if@headerraggedleft
\DeclareOption{photoleft}{\@photolefttrue \chardef\photo@optB=1\relax}
% Rectangular photo:
\newif\if@normalphoto
\DeclareOption{normalphoto}{\@normalphototrue \chardef\photo@optB=1\relax}
% CV header text alignment options:
%-------------------------------
\DeclareOption{header=raggedleft}{\@headerraggedlefttrue \chardef\header@optA=1\relax}
\DeclareOption{header=raggedright}{\@headerraggedleftfalse \chardef\header@optB=1\relax}
\DeclareOption{header=center}{\@centeredtrue \chardef\header@optC=1\relax}
%
% Name display:
%-------------------------------
% Include vonname:
\newif\if@displayvon
\DeclareOption{vonname=true}{\@displayvontrue}
% Displaystyles:
%
% Lastname, Firstname Vonname
\newif\if@lastfirstvonname
\DeclareOption{namedisplay=lastfirstvon}{\@lastfirstvonnametrue \chardef\name@optA=1\relax}
% Lastname Firstname
\DeclareOption{namedisplay=lastfirst}{\@lastfirstvonnametrue \chardef\name@optB=1\relax}
% Vonname Lastname, Firstname
\newif\if@vonlastfirstname
\DeclareOption{namedisplay=vonlastfirst}{\@vonlastfirstnametrue \chardef\name@optC=1\relax}
% Firstname Lastname, Vonname
\newif\if@firstlastvonname
\DeclareOption{namedisplay=firstlastvon}{\@firstlastvonnametrue \chardef\name@optD=1\relax}
% Firstname Lastname
\newif\if@firstlastonly
\DeclareOption{namedisplay=firstlast}{\@firstlastonlytrue \chardef\name@optE=1\relax}
%
% Bibliography options:
%-------------------------------
% Skip bibliography code
\newif\if@nobib
\DeclareOption{bib=false}{\@nobibtrue \chardef\bib@optA=1\relax}
% "Normal" bibliograpy style
\newif\if@publistnormal
\DeclareOption{bib=normal}{\@publistnormaltrue \chardef\bib@optB=1\relax}
% Higlight your name in bibliography
\newif\if@publisthighlight
\DeclareOption{bib=highlightname}{\@publisthighlighttrue \chardef\bib@optC=1\relax}
% "Normal" bibliography but hide your name
\newif\if@publisthideonly
\DeclareOption{bib=hidenameonly}{\@publisthideonlytrue \chardef\bib@optD=1\relax}
%
% CV pages options:
%-------------------------------
% More than 2 pages:
\newif\if@longCV
\DeclareOption{multipleCVs}{\@longCVtrue}
% Display name at second page:
\newif\if@nameheader
\DeclareOption{page2=displayname}{\@nameheadertrue}
% Display page number at second page:
\newif\if@pageheader
\newif\if@pagefooter
\newif\if@pageclassic
\DeclareOption{page2=pagenumtop}{\@pageheadertrue}
\DeclareOption{page2=pagenumbottom}{\@pagefootertrue}
\DeclareOption{page2=pagenumclassic}{\@pageclassictrue}
% Display both:
\DeclareOption{page2=display}{\@nameheadertrue \@pageheadertrue}
%
% Pass other options to article class
%-------------------------------
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
%
% Mutually exclusive options error:
%-------------------------------
\ExplSyntaxOn
\prop_gput:Nnn \g_msg_module_type_prop { CV } { Class }
\msg_new:nnnn { CV } { exclusive options } { Current~class~options~are~not~compatible. } { Try~removing~similar~options. }
%
\ifnum\numexpr\photo@optA+\photo@optB>\@ne %
    { \msg_error:nn { CV } { exclusive options } }
\fi%
\ifnum\numexpr\header@optA+\header@optB+\header@optC>\@ne%
    { \msg_error:nn { CV } { exclusive options } }
\fi%
\ifnum\numexpr\name@optA+\name@optB+\name@optC+\name@optD+\name@optE>\@ne%
    { \msg_error:nn { CV } { exclusive options } }
\fi%
\ifnum\numexpr\bib@optA+\bib@optB+\bib@optC+\bib@optD+\bib@optE>\@ne%
    { \msg_error:nn { CV } { exclusive options } }
\fi%
\ExplSyntaxOff
%
%................................................................
%
%                           Packages
%_______________________________________________________________
\RequirePackage[T1]{fontenc}
\RequirePackage{geometry}           % to adjust margins
\RequirePackage{fontawesome}        % symbols (phone, e-mail, etc.)
\RequirePackage{xcolor}             % colours
\RequirePackage[most]{tcolorbox}    % Summary box
\RequirePackage{graphicx}           % Picture
\RequirePackage{dashrule}           % Dotted line
\RequirePackage{hyperref}           % Clickable links
\RequirePackage{tabularray}         % Used for cvtable
\RequirePackage{adjustbox}          % Summary box (environment varwidth)
\RequirePackage{fancyhdr}           % For page limit and header 2nd page
%................................................................
%
%                             Name
%_______________________________________________________________
% Commands for providing names, will be used in bibliography later.
\newcommand{\firstname}[1]{\def\@firstname{#1}}
\newcommand{\vonname}[1]{\def\@vonname{#1}}
\newcommand{\lastname}[1]{\def\@lastname{#1}}
% Options for name display:
\if@lastfirstvonname
    \if@displayvon
        \def\@name{\@lastname,\ \@firstname\ \@vonname}
    \else
        \def\@name{\@lastname,\ \@firstname}
    \fi%
\else
    \if@vonlastfirstname
        \if@displayvon
            \def\@name{\@vonname\ \@lastname,\ \@firstname}
        \else
            \def\@name{\@lastname,\ \@firstname}
        \fi%
    \else
        \if@firstlastvonname
            \if@displayvon
                \def\@name{\@firstname\ \@lastname,\ \@vonname}
            \else
                \def\@name{\@firstname\ \@lastname}
            \fi%
        \else
            \if@firstlastonly
                \def\@name{\@firstname\ \@lastname}
            \else
                \if@displayvon
                    \def\@name{\@firstname\ \@vonname\ \@lastname}
                \else
                    \def\@name{\@firstname\ \@lastname}
                \fi%
            \fi%
        \fi%
    \fi%
\fi%
%
%................................................................
% 
%                           Colours 
%_______________________________________________________________
\definecolor{darkgray}{rgb}{0.45,0.45,0.45}
\definecolor{lightgray}{rgb}{0.95,0.95,0.95}
\definecolor{Overleaf_green}{HTML}{46A247}
% Colour names used later in .cls file:
\colorlet{icons}{Overleaf_green}
\colorlet{soft_text}{darkgray}
\colorlet{background_color}{lightgray} % for summary box
% If you want another colour, you can do this in the preamble
% using \colorlet{icons}{<some colour>} or similarly for 
% soft_text and background_color
%
% Gray (soft) text:
\newcommand{\softtext}[1]{\textcolor{soft_text}{#1}}
\newcommand{\softbullet}{\softtext{\small\textbullet}\hspace{0.5em}}
%................................................................
%
%                   Document adjustments
%_______________________________________________________________
\geometry{%
        left=9mm,
        right=9mm,
        bindingoffset=0mm,
        top=10mm,
        bottom=10mm
    }
% Horizontal lines:
\newcommand{\linia}{\rule{\linewidth}{0.5pt}}
\newcommand{\dotline}{\noindent\textcolor{soft_text}{\hdashrule{\linewidth}{0.6pt}{0.5ex}}\medskip}
% Remove colour boxes around links:
\hypersetup{hidelinks}
%
% Page limit:
\newcounter{pagelimit}
\setcounter{pagelimit}{2}
%
% Command for the word "page" in different languages:
% (overwritten by babel)
\providecommand{\pagename}{Page}
%
% Setting up page style and page limit error:
\ExplSyntaxOn
\msg_new:nnnn { CV } { pagenumber } 
    { Page~limit:~\thepagelimit\ ~pages,~exceeded.} { Use~option~'multipleCVs'~to~exceed~page~limit. }
\msg_new:nnnn { CV } { footer conflict }
    { Current~page~number~options~can~not~be~combined } { Chose~one~option }

\fancypagestyle{CVpages}{
\fancyhf{}% clears page number
\renewcommand{\headrulewidth}{0pt}
\fancyfoot{
\if@pagefooter
    \if@pageclassic
        \msg_error:nn { CV } { footer conflict }
    \else%
        \ifodd\value{page}\else%
        \softtext{\hfill \page\ 2}
        \fi%
    \fi%
\else%
    \if@pageclassic
        \ifodd\value{page}\else%
        \softtext{\hfill 2 \hfill}
        \fi%
    \fi%
\fi%
}%
\fancyhead{%
\if@longCV
\else
    \ifnum\value{page}>\thepagelimit
        { \msg_fatal:nn {CV}{pagenumber} }
        {}
    \fi%
\fi%
\ifodd\value{page}
\else
    \if@nameheader
        \if@pageheader
            \softtext{\@name \hfill \pagename\ ~2}
        \else
            \softtext{\@name}
        \fi%
    \else
        \if@pageheader
            \softtext{\hfill \pagename\ ~2}
        \fi%
    \fi%
\fi%
}}%
%
% Some error messages when having multiple page displays:
\msg_new:nnnn {CV} { pagedisplay } { Currently~displaying~multiple~page~numbers. } { Remove~conflicting~options~or~ignore~this~warning. }
%
\if@pageclassic\if@pageheader
    { \msg_error:nn {CV} { pagedisplay } }
\fi\fi%
%
\if@pagefooter\if@pageheader
    { \msg_error:nn {CV} { pagedisplay } }
\fi\fi%
%
\ExplSyntaxOff
%
% Command for putting in blank pages:
\newcommand\blankpage[1][1]{%
    \foreach \x in {1,...,#1}{%
    \clearpage
    \null
    \thispagestyle{CVpages}%
    \clearpage}
}%
%
%................................................................
% 
%                   CV header/ personal info
%_______________________________________________________________
% Defining some symbols:
\newcommand{\emailsymbol}{\faAt}
\newcommand{\phonesymbol}{\faPhone}
\newcommand{\locationsymbol}{\faMapMarker}
\newcommand{\mailsymbol}{\faEnvelope}
\newcommand{\calendarsymbol}{\faCalendar}
\newcommand{\birthdaysymbol}{\faBirthdayCake}
% How information is displayed in header:
\newcommand{\printinfo}[2]{\mbox{\textcolor{icons}{\normalfont #1}\hspace{1em}\textcolor{soft_text}{#2}\hspace{2em}}}
% Commands for providing personal information:
\newcommand{\tagline}[1]{\def\@tagline{#1}}
\newcommand{\photo}[2]{\def\@photo{#2}\def\@photodiameter{#1}}
\newcommand{\email}[1]{\printinfo{\emailsymbol}{\hspace{-0.2em}\href{mailto:#1}{#1}}}
\newcommand{\phone}[1]{\printinfo{\phonesymbol}{\hspace{-0.1em}#1}}
\newcommand{\location}[1]{\printinfo{\locationsymbol}{#1}}
\newcommand{\mailaddress}[1]{\printinfo{\mailsymbol}{\hspace{-0.4em}#1}}
\newcommand{\birthday}[1]{\printinfo{\birthdaysymbol}{\hspace{-0.4em}#1}}
% Storing personal info for \makecvheader command:
\newcommand{\personalinfo}[1]{\def\@personalinfo{#1}}
%
% Command for printing cv header (similar to \maketitle)
\newcommand*\cvheader@photo
  {%
    \if@nophoto
        % Don't include photo
    \else
        \begin{minipage}{\@photodiameter}%
        \if@normalphoto
          \includegraphics[width=\linewidth]{\@photo}%
        \else
          \tikz
            \path[fill overzoom image={\@photo}]circle[radius=0.5\linewidth];%
        \fi
        \end{minipage}%
    \fi%
  }
%
\newcommand*\cvheader@text[1]
  {%
    \begin{minipage}{#1}%
      \if@centered
          \centering
      \fi
      \if@headerraggedleft
          \raggedleft
      \fi
      {\Huge\bfseries\@name\par}%
      \medskip
      {\large\@tagline\par}%
      \medskip
      {\footnotesize\@personalinfo\par}%
    \end{minipage}%
  }
%
\newcommand{\makecvheader}{%
  \begingroup
    \ifdef\@photodiameter{}{\@nophototrue}%
    \if@photoleft
      \cvheader@photo
      \hspace{1cm}
      \hfill
    \fi
    \if@nophoto
      \cvheader@text{\dimexpr\linewidth-2em\relax}%
    \else
      \cvheader@text{\dimexpr\linewidth-\@photodiameter-2em\relax}%
    \fi
    \if@photoleft\else
      \hfill
      \cvheader@photo
    \fi
    \par
  \endgroup
  \vspace{\baselineskip}%
  \noindent\linia
  \medskip
}%
%................................................................
%
%               Sections and environments
%_______________________________________________________________
% Section:
\renewcommand{\section}{\@ifstar\@section\@@section}
% Starred section command (\section*{ })
% This is needed to fix bibliography title(s).
\newcommand{\@section}[1]{%
  \bigskip%
  {\LARGE\MakeUppercase{#1}}\\[-1ex]%
  \linia\medskip
}%
% Unstarred section command (\section{ })
\newcommand{\@@section}[1]{%
  \bigskip%
  {\LARGE\MakeUppercase{#1}}\\[-1ex]%
  \linia\medskip
}%
% Subsection:
\renewcommand{\subsection}[1]{%
  \smallskip%
  {\large\bfseries{#1}\par}\medskip
}%
% CV_table (3 column style CV entries):
\newenvironment{CV_table}{%
    \par\addvspace{\topsep}\noindent
    \begin{tblr}{%
    colspec={@{} t{2.cm} | X[l,3.8] X[l,3.5] @{}},
    column{1} = {font=\bfseries},
    width=1.1\textwidth,
    colsep = 10pt,
    rowsep=0.3\baselineskip}%
    }%
    { \end{tblr} \par\addvspace{\topsep} }
% CV_text (2 column style CV entries):
\newenvironment{CV_text}{%
    \par\addvspace{\topsep}\noindent
    \begin{tblr}{%
    colspec={@{} t{1.73cm} | X[l,7.3] @{}},
    column{1} = {font=\bfseries},
    width=1.1\textwidth,
    colsep = 15pt,
    rowsep=0.5\baselineskip}%
    }%
    { \end{tblr} \par\addvspace{\topsep} }
% Date and location for CV_table:
\newcommand{\CVdate}[1]{%
    \begin{tblr}{colspec={X[c,1] X[10]},width=\linewidth}\textcolor{icons}{\calendarsymbol} & #1\end{tblr}
}%
\newcommand{\CVlocation}[1]{%
    \begin{tblr}{colspec={X[1,c] X[10]},width=\linewidth}\textcolor{icons}{\locationsymbol} & #1\end{tblr}
}%
\newcommand{\CVevent}[2]{%
    \begin{tblr}{colspec={X[1,c] X[10]},width=\linewidth}\textcolor{icons}{\calendarsymbol} & #1 \\
    \textcolor{icons}{\locationsymbol} & #2\end{tblr}
}%
%
% Itimize and similar
\newcommand{\veritem}[1]{\softbullet#1\hspace{1em}}
  \renewcommand{\labelitemi}{\softtext{\small\textbullet}}
%   \renewcommand{\labelitemii}{\softtext{\textdash}}
%   \renewcommand{\labelitemiii}{\softtext{$\circ$}}
\newenvironment{itemlist}{
    \begin{itemize}
    \setlength{\itemsep}{5pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
}{\end{itemize}}
%
% Summary box:
\newtcolorbox{emph_box}[1][]{%
    enhanced,
    before skip=2mm,after skip=2mm, % space above and below box
    boxrule=0.6pt, % line thickness
    colback=background_color, colframe=icons, % Colors
    attach boxed title to top left={xshift=0cm,yshift*=0mm-\tcboxedtitleheight},
    varwidth boxed title*=-3cm,
    % The titlebox:
    boxed title style={frame code={%
        \path[left color=icons,right color=icons, middle color=icons]
        (frame.north west) [sharp corners] -- 
        (frame.north east) [rounded corners=1.5mm] -- 
        (frame.south east) [sharp corners] -- 
        (frame.south west) [rounded corners=1.5mm] -- 
        cycle;
        },interior engine=empty,
    },
    % Alternative titlebox definition (does the same thing):
    % boxed title style={sharp corners=uphill, colback=icons},
    width=\textwidth,
    arc is curved,
    arc = 1.5mm, % radius of rounded corners
    fonttitle=\bfseries, 
    title={#1}
}%
\newenvironment{Summary}[1]{%
    \begin{emph_box}[#1]
    }{%
    \end{emph_box}
}%

% Links environment (under header):
\newenvironment{linkheader}{%
    \begin{center}
    \footnotesize
    \vspace{-1.2\baselineskip}
    }{%
    \end{center}
    \vspace{-0.6\baselineskip}
}%
% Some commands for providing links
\newcommand{\linkedinsymbol}{\faLinkedin}
\newcommand{\githubsymbol}{\faGithub}
\newcommand{\homepagesymbol}{\faChain}
\newcommand{\twittersymbol}{\faTwitter}
\newcommand{\twitter}[1]{\printinfo{\twittersymbol}{\href{https://twitter.com/#1}{@#1}}}
\newcommand{\linkedin}[1]{\printinfo{\linkedinsymbol}{\href{https://#1}{#1}}}
\newcommand{\github}[1]{\printinfo{\githubsymbol}{\href{https://#1}{#1}}}
\newcommand{\homepage}[1]{\printinfo{\homepagesymbol}{\href{https://#1}{#1}}}
% General command for providing links in link header:
\newcommand{\ProvideSymbolLink}[2]{\printinfo{#2}{\href{https://#1}{#1}}}
%................................................................
%
%                       Language section
%_______________________________________________________________
% rating circles:
\newcommand{\ratingmarker}{\faCircle}
\newcommand{\CVrating}[4][]{%
    #2\hfill#1
    \foreach \x in {1,...,#4}{%
    \space{\ifnumgreater{\x}{#3}{\color{background_color}}{\color{icons}}\ratingmarker}}\par%
}%
\newcommand{\LngLvlWords}[2]{%
    #1\hfill \textit{#2}\par%
}%
%
\newcommand{\LngLvlILR}[2]{%
    \CVrating[#2\softtext{*}]{#1}{#2}{5}
}%
%
\ExplSyntaxOn
% Command for CEFR rating:
\msg_new:nnnn { CEFR Rating } { unsupported-argument }
    % Error when not using one of the CEFR ratings
  { Unsupported~ entry~ field~ `#1'.}
  { Accepted~entries:~'A1',~'A2',~'B1',~'B2',~'C1'~'C2'~or~'0'. }

\NewDocumentCommand \LngLvlCEFR { m m }
    { \Lng_CEFR_check:nn {#1} {#2} }

\cs_new_protected:Npn \Lng_CEFR_check:nn #1#2
  {
    \str_case:nnF {#2}
    {% Displaying the language proficiency levels:
        {A1}{ \CVrating[\textit{#2}\softtext{*}]{#1}{1}{6} }
        {A2}{ \CVrating[\textit{#2}\softtext{*}]{#1}{2}{6} }
        {B1}{ \CVrating[\textit{#2}\softtext{*}]{#1}{3}{6} }
        {B2}{ \CVrating[\textit{#2}\softtext{*}]{#1}{4}{6} }
        {C1}{ \CVrating[\textit{#2}\softtext{*}]{#1}{5}{6} }
        {C2}{ \CVrating[\textit{#2}\softtext{*}]{#1}{6}{6} }
        {0}{ \CVrating{#1}{0}{6} }
    }
    {% Error for unrecognised proficiency level:
        \msg_error:nnn { CEFR Rating } { unsupported-argument } {#2}
    }
  }
  
% Command for CEFR text
\msg_new:nnnn { LngTextCEFR } { unsupported-language }
    % Error when not using an accepted language for command
  { Language~`\languagename'~ not~ supported~ for~ ` \token_to_str:N \LngTextCEFR '. }
  { ` \token_to_str:N \LngTextCEFR '~ currently~ supports:~ english,~ and~ norwegian~(bokmål~and~nynorsk). }
 
\prop_new:N\g_language_text_CEFR
\prop_gset_from_keyval:Nn \g_language_text_CEFR
 {
   english = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Using~ CEFR~ rating~ for~ language~ proficency.}} },
   norsk = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Med~ CEFR~ som~ mål~ på~ språkkunnskaper.}} },
   nynorsk  = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Med~ CEFR~ som~ mål~ på~ språkkunnskapar.}} }
 }
\newcommand{\LngTextCEFR}
 {
   \prop_get:NVNTF \g_language_text_CEFR \languagename \l_tmpa_CEFR_tl
     { \l_tmpa_CEFR_tl }
     { \msg_error:nn { LngTextCEFR } {unsupported-language} }
 }

% Command for ILR text
\msg_new:nnnn { LngTextILR } { unsupported-language }
    % Error when not using an accepted language for command
  { Language~`\languagename'~ not~ supported~ for~ ` \token_to_str:N \LngTextILR '. }
  { ` \token_to_str:N \LngTextILR '~ currently~ supports:~ english,~ and~ norwegian~(bokmål~and~nynorsk). }
 
\prop_new:N\g_language_text_ILR
\prop_gset_from_keyval:Nn \g_language_text_ILR
 {
   english = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Using~ ILR~ rating~ for~ language~ proficency.}} },
   norsk = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Med~ ILR~ som~ mål~ på~ språkkunnskaper.}} },
   nynorsk  = { \vspace{0.5\baselineskip}{\footnotesize\softtext{*Med~ ILR~ som~ mål~ på~ språkkunnskapar.}} }
 }
\newcommand{\LngTextILR}
 {
   \prop_get:NVNTF \g_language_text_ILR \languagename \l_tmpa_ILR_tl
     { \l_tmpa_ILR_tl }
     { \msg_error:nn { LngTextILR } {unsupported-language} }
 }

\ExplSyntaxOff
%
%................................................................
%
%                           Quote
%_______________________________________________________________
% Produces colored italic text inside quotation marks (`` '')
\renewenvironment{quote}[1][icons]{%
    \begingroup\color{#1}\itshape``
    }{%
    ''\endgroup
}%
%................................................................
%
%                           Referee
%_______________________________________________________________
\newcommand{\CVref}[4]{%
    \textbf{#1} \\ 
    #3 \\ 
    \textcolor{icons}{\emailsymbol} \hspace{3pt} \href{mailto:#1}{#2} \\ 
    %\textcolor{icons}{\mailsymbol} \hspace{3pt} #3
    \vspace{\baselineskip}
}%
%................................................................
%
%                   Side bar / second column
%_______________________________________________________________
\newenvironment{CVsidebar}{%
        \begin{minipage}[t]{5cm}\raggedright
    }{%
        \end{minipage}
    }%
\newenvironment{CVbody}{%
        \hspace{-0.5cm}\begin{minipage}[t]{10cm}\raggedright
    }{%
        \end{minipage}\hspace{1cm}
    }%
%................................................................
%
%                   Publications using bibLaTeX
%_______________________________________________________________
\if@nobib
    % No bibliography, skips code below.
\else
% Importing bibLaTeX:
\if@publistnormal
    \RequirePackage[%
            backend=biber,
            %bibstyle=publist,
            style=authoryear,
            hyperref=auto
        ]{biblatex}
    \AtEveryBibitem{\makebox[\bibhang][l]{\softbullet}}
\else
    \if@publisthideonly
        \RequirePackage[%
                %hlyear=false,
                backend=biber,
                bibstyle=publist,
                labeldateparts=false,
                hyperref=auto
            ]{biblatex}
        \defbibenvironment{bibliography}
          {\list
             {\labelitemfont\softbullet}
             {\setlength{\leftmargin}{\bibhang}%
              \setlength{\itemsep}{\bibitemsep}%
              \setlength{\parsep}{\bibparsep}%
              \def\makelabel##1{\hss\llap{##1}}}}%
          {\endlist}
          {\item}
        %\providecommand*\plyearhl[1]{#1}
    \else
        \if@publisthighlight
            \RequirePackage[%
                    plauthorhandling=highlight, % 
                    backend=biber,
                    bibstyle=publist,
                    labeldateparts=false,
                    hyperref=auto
                ]{biblatex}
            \defbibenvironment{bibliography}
              {\list
                 {\labelitemfont\softbullet}
                 {\setlength{\leftmargin}{\bibhang}%
                  \setlength{\itemsep}{\bibitemsep}%
                  \setlength{\parsep}{\bibparsep}%
                  \def\makelabel##1{\hss\llap{##1}}}}%
              {\endlist}
              {\item}
        \else
            \RequirePackage[%
                    backend=biber,
                    bibstyle=publist,
                    labeldateparts=false,
                    hyperref=auto
                ]{biblatex}
            \defbibenvironment{bibliography}
              {\list
                 {\labelitemfont\softbullet}
                 {\setlength{\leftmargin}{\bibhang}%
                  \setlength{\itemsep}{\bibitemsep}%
                  \setlength{\parsep}{\bibparsep}%
                  \def\makelabel##1{\hss\llap{##1}}}}%
              {\endlist}
              {\item}
        \fi
    \if@displayvon
        \plauthorname[\@firstname][\@vonname]{\@lastname}
    \else
        \plauthorname[\@firstname]{\@lastname}
    \fi
    \fi
\fi


% Changing entries and heading
\defbibheading{pubtype}{\subsection{#1}}
\renewcommand{\bibsetup}{\vspace*{-\baselineskip}}
\setlength{\bibitemsep}{0.25\baselineskip}
%
% Remove "in" from journal when no journal is provided
\renewbibmacro*{in:}{%
  \iffieldundef{journaltitle}
    {}
    {\printtext{\bibstring{in}\intitlepunct}}
}%
% Command for bibliography subtitle. 
% ( i.e. \printbibliography[title={ \pubtitle{<arg>} }] )
%-------------------------------
\ExplSyntaxOn

% Error messages:
\msg_new:nnn { pubtitle } { extraneous-optional }
  {% When passing optional arguments and not using {custom}
    \exp_not:N \pubtitle
    only~ accepts~ optional~ arguments~ if~ you~ use~ `custom'~ as~ a~
    mandatory~ argument.
  }
\msg_new:nnnn { pubtitle } { unsupported-argument }
    % When not using an accepted bibliography entry
  { Unsupported~ entry~ field~ `#1'~ for~ bibliography. }
  { Perhaps~ you~ meant~ `\token_to_str:N \pubtitle[<text>][<icon>]{custom}'. }

% The command (document interface):
\NewDocumentCommand \pubtitle { o o m }
  { \pubtitle_pubtitle:nne {#1} {#2} { \str_foldcase:n {#3} } }

% Default values for \pubtitle{custom}:
\tl_new:N \l__pubtitle_default_custom_icon_tl
\tl_new:N \l__pubtitle_default_custom_title_tl
\tl_set:Nn \l__pubtitle_default_custom_icon_tl { \faFileTextO }
\tl_set:Nn \l__pubtitle_default_custom_title_tl { Publications }

% The command (internal code):
\cs_new_protected:Npn \pubtitle_pubtitle:nnn #1#2#3
  {
    \str_case:nnTF {#3}
      {% Accepted arguments (without custom):
        { book }    { \pubtitle_symbolheading:nn \faBook     { Books } }
        { article } { \pubtitle_symbolheading:nn \faFileText { Articles } }
        { conferance }{ \pubtitle_symbolheading:nn \faCommenting { Conferences } }
        { online }{ \pubtitle_symbolheading:nn \faLaptop { Online ~ Resources } }
        { thesis }{ \pubtitle_symbolheading:nn \faMortarBoard { Theses } }
        { report }{ \pubtitle_symbolheading:nn \faFilePdfO { Reports } }
        { inproceedings }{ \pubtitle_symbolheading:nn \faGroup { Proceedings } }
        { manual }{ \pubtitle_symbolheading:nn \faWrench { Manuals } }
        { phdthesis }{ \pubtitle_symbolheading:nn \faMortarBoard { Phd ~ Thesis } }
        { masterthesis }{ \pubtitle_symbolheading:nn \faMortarBoard { Mater ~ Thesis } }
        { patent }{ \pubtitle_symbolheading:nn \faCopyright { Patents } }
        { datatype }{ \pubtitle_symbolheading:nn \faDatabase { Raw ~ Data } }
        { software }{ \pubtitle_symbolheading:nn \faCode { Software } }
      }
      { % Error when optional arguments but not using custom:
        \tl_if_novalue:nF {#1}
          { \msg_error:nn { pubtitle } { extraneous-optional } }
      }
      { % Custom entry:
        \str_if_eq:nnTF {#3} { custom }
          {
            \tl_if_novalue:nTF {#2}
              {
                \tl_if_novalue:nTF {#1}
                  { % If no optionals are given, return default values:
                    \pubtitle_symbolheading:nn
                      \l__pubtitle_default_custom_icon_tl
                      \l__pubtitle_default_custom_title_tl
                  }
                  { % when only one (1) optional argument is specified:
                    \tl_if_single:nTF {#1}
                      { % a single token/braced group (symbol):
                        \pubtitle_symbolheading:nn
                          #1
                          \l__pubtitle_default_custom_title_tl
                      }
                      { % multiple tokens/braced groups (text):
                        \pubtitle_symbolheading:nn
                          \l__pubtitle_default_custom_icon_tl
                          {#1}
                      }
                  }
              }
              { \pubtitle_symbolheading:nn {#2} {#1} } % two optional arguments.
          }
          { \msg_error:nnn { pubtitle } { unsupported-argument } {#3} } 
      }
  }
\cs_generate_variant:Nn \pubtitle_pubtitle:nnn { nne }
\cs_new_protected:Npn \pubtitle_symbolheading:nn #1#2
  {% Typsetting, i.e. colours, textfont, indents/spaces etc.
    \group_begin:
      \hspace{-1.3\parindent}
      \large
      \textcolor { icons } {#1}
      \skip_horizontal:n { 10pt }
      \textbf {#2}
    \group_end:
  }
\ExplSyntaxOff
\fi
%................................................................
%
%                   At begin document
%_______________________________________________________________
\AtBeginDocument{%
  \pagestyle{CVpages} % Blank pages (no page numbers etc.)
}%
%................................................................
\endinput
%
%---------------------------------------------------------------------------------------------------------------------
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%                           Appendix 
%_______________________________________________________________
% ASCII-art created with ASCII art generator (name of style used: Georgia11) 
% Link to ASCII art generator: https://www.kammerl.de/ascii/AsciiSignature.php
%
%       File history:
%-------------------------------
% -- First version created in 2022
%
%    Links and resources:
%-------------------------------
% -- Fontawsome symbols (CTAN documentation):
%       * https://www.ctan.org/pkg/fontawesome
% -- Learn expl3 syntax:
%       * https://www.latex-project.org/news/2020/11/09/l3-tutorial/
%       * https://ctan.org/pkg/l3kernel
% -- Book (about job application, in norwegian):
%       * Jobbsøkerkoden by Sverre Haugen and Olav Schewe. Published by Universitetsforlaget 2021. ISBN: 978-82-15-02533-9
%
%    TeX Stack Exchange users:
%-------------------------------
% Link to TeX.SE: https://tex.stackexchange.com/
% I would like to thank these TeX Stack Exchange (TeX.SE) users for helping me
% with parts of my LaTeX code:
% 
% -- Skillmon                           
%       \pubtitle command, optional parameters for custom,
%       redefining of \makecvheader to be compatible with photoleft option,
%       make CV module appear as class ("Class CV error:"").
%       In accordance with his Beer-ware licence, I will
%       buy him a beer if I meet him some day.
% -- egreg
%       \pubtitle command, error messages
% -- moewe 
%       bibLaTeX section error (because of \section*)
%       and removing numbers from biblatex publist.
% -- Celdor
%       tabularray inside tabularray error in CV table
% -- samcarter_is_at_topanswers.xyz  
%       rounded corners titlebox in summary box
% -- Ignasi 
%       rounded corners titlebox in summary box
% -- Werner, user187802 and cabohah
%       clarifying why my if else for name display didn't work
%       (I did not use \fi correctly)